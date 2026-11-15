"""Version-3 generic scalar rules and bounded constraint plans."""

from bisect import bisect_right
from copy import deepcopy
from datetime import date
from decimal import Decimal, ROUND_HALF_EVEN, localcontext
import math
import re

from . import recipe as rules

FORMAT = 'ravel-single-table/3'
PARAMETERS = dict(normal={'mean','sd','places'}, boolean={'probability'},
                  date={'minimum','maximum'}, date_sequence={'start','step'},
                  category_quota={'values','counts','missing_count','scope'})


def day(value, path):
    if not isinstance(value,str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}',value):
        rules.fail(path,'Use an ISO calendar date, YYYY-MM-DD.')
    try:
        return date.fromisoformat(value).toordinal()
    except ValueError:
        rules.fail(path,'Use a valid calendar date in years 0001–9999.')


def project(field, path, count, version):
    candidate=deepcopy(field)
    kind=field.get('kind')
    if 'unique' in field and version==FORMAT:
        if type(field['unique']) is not bool:
            rules.fail(path+'.unique','Unique must be true or false.')
        candidate.pop('unique')
    if not isinstance(kind,str) or kind not in PARAMETERS:
        return candidate
    if version!=FORMAT:
        rules.fail(path+'.kind','This rule requires ravel-single-table/3; keep the original recipe and save a separate copy.')
    rules.keys(candidate,{'id','name','kind','missing_probability'}|PARAMETERS[kind],path)
    if kind=='normal':
        rules.decimal(field['mean'],path+'.mean')
        if rules.decimal(field['sd'],path+'.sd',0)<=0:
            rules.fail(path+'.sd','Standard deviation must be positive.')
        rules.integer(field['places'],path+'.places',0,6)
    elif kind=='boolean':
        rules.decimal(field['probability'],path+'.probability',0,1)
    elif kind=='date':
        if day(field['minimum'],path+'.minimum')>day(field['maximum'],path+'.maximum'):
            rules.fail(path+'.minimum','Minimum date must not exceed maximum date.')
    elif kind=='date_sequence':
        start=day(field['start'],path+'.start')
        step=rules.integer(field['step'],path+'.step',-36600,36600)
        if not 1<=start+max(0,count-1)*step<=date.max.toordinal():
            rules.fail(path+'.start','Date sequence would leave years 0001–9999.')
    else:
        values=field['values']
        if not isinstance(values,list) or not 1<=len(values)<=100:
            rules.fail(path+'.values','Use 1–100 distinct categories.')
        for value in values:
            rules.text(value,path+'.values')
        if len(set(values))!=len(values):
            rules.fail(path+'.values','Category values must be distinct.')
        if not isinstance(field['counts'],list) or len(field['counts'])!=len(values):
            rules.fail(path+'.counts','Provide one exact count per category.')
        for number in field['counts']:
            rules.integer(number,path+'.counts',0,100_000)
        rules.integer(field['missing_count'],path+'.missing_count',0,100_000)
        if field['scope'] not in ('generated','final'):
            rules.fail(path+'.scope','Choose generated or final quota scope.')
        if rules.decimal(field['missing_probability'],path+'.missing_probability',0,1):
            rules.fail(path+'.missing_probability','Use the exact missing count with quotas; missing probability must be zero.')
    return dict(id=field['id'],name=field['name'],kind='constant',value='validated rule',
                missing_probability=field['missing_probability'])


def retained_source(document, field):
    if 'sample' not in document or document['sample']['mode']!='extend':
        return []
    from .sample import context
    _,rows,retained,_=context(document)
    index=document['sample']['source_fields'].get(field['id'])
    return [row[index] if index is not None else '' for row in rows[:retained]]


def quota_counts(document, field, count):
    counts=field['counts'][:]+[field['missing_count']]
    expected=document['table']['row_count'] if field['scope']=='final' else count
    path='table.fields.'+str(document['table']['fields'].index(field))+'.counts'
    if sum(counts)!=expected:
        rules.fail(path,f'Exact counts including missing must total {expected:,} for {field["scope"]} scope.')
    if field['scope']=='final':
        for value in retained_source(document,field):
            if value=='' or value is None:
                index=len(counts)-1
            elif value in field['values']:
                index=field['values'].index(value)
            else:
                rules.fail(path,f'Retained value {value!r} is outside the declared quota categories.')
            counts[index]-=1
            if counts[index]<0:
                rules.fail(path,'Retained originals already exceed a final quota; originals cannot be changed.')
    assert sum(counts)==count
    return counts


def domain(field):
    kind=field['kind']
    if kind=='integer':
        return field['minimum'],field['maximum'],1
    if kind=='decimal':
        scale=10**field['places']
        return int(Decimal(field['minimum'])*scale),int(Decimal(field['maximum'])*scale),scale
    return day(field['minimum'],'minimum'),day(field['maximum'],'maximum'),1


def unique_plan(document,field,count):
    path='table.fields.'+str(document['table']['fields'].index(field))+'.unique'
    if rules.decimal(field['missing_probability'],path,0,1):
        rules.fail(path,'Unique generation requires zero missing probability.')
    if field['kind'] in {'id','text_id'}:
        return None
    if field['kind'] not in {'integer','decimal','date'}:
        rules.fail(path,'Unique is supported for integer, decimal, date and identifier rules only.')
    low,high,scale=domain(field)
    original=[]
    for value in retained_source(document,field):
        if value=='':
            rules.fail(path,'Retained unique values must be nonmissing.')
        if field['kind']=='date':
            typed=day(value,path)
        else:
            if not re.fullmatch(r'-?\d+(?:\.\d+)?',value):
                rules.fail(path,'Retained cells must match the declared numeric type for final uniqueness.')
            number=Decimal(value)
            if abs(number)>rules.LIMIT or number*scale!=int(number*scale):
                rules.fail(path,'Retained cells must be supported values on the declared numeric grid.')
            typed=int(number*scale)
        original.append(typed)
    if len(set(original))!=len(original):
        rules.fail(path,'Retained originals already contain duplicate typed values.')
    excluded=sorted(value-low for value in original if low<=value<=high)
    capacity=high-low+1-len(excluded)
    if count>capacity:
        rules.fail(path,f'Unique domain has {capacity:,} available values for {count:,} new rows.')
    return low,high,excluded


def preflight(document,count):
    with localcontext() as context:
        context.prec=40
        for field in document['table']['fields']:
            if field.get('unique'):
                unique_plan(document,field,count)
            if field['kind']=='category_quota':
                quota_counts(document,field,count)


def rounded_normal(raw,places):
    if not math.isfinite(raw) or abs(raw)>rules.LIMIT:
        rules.fail('result','Normal rule produced an out-of-range value; no result was published.')
    rounded=Decimal(str(raw)).quantize(Decimal(1).scaleb(-places),rounding=ROUND_HALF_EVEN)
    if abs(rounded)>rules.LIMIT:
        rules.fail('result','Rounded normal output is outside the supported range.')
    return rounded


def generated_recipe(document,count):
    candidate=deepcopy(document)
    candidate.pop('sample',None)
    candidate['table']['row_count']=count
    for original,field in zip(document['table']['fields'],candidate['table']['fields']):
        if field['kind']=='category_quota':
            counts=quota_counts(document,original,count)
            field.update(counts=counts[:-1],missing_count=counts[-1],scope='generated')
    return candidate


def column(document,field,count,random,source_document=None):
    kind=field['kind']
    original=document if source_document is None else source_document
    if field.get('unique') and kind not in {'id','text_id'}:
        low,high,excluded=unique_plan(original,field,count)
        values=[]
        for rank in random.sample(range(high-low+1-len(excluded)),count):
            left,right=rank,rank+len(excluded)
            while left<right:
                middle=(left+right)//2
                if middle-bisect_right(excluded,middle)<rank:
                    left=middle+1
                else:
                    right=middle
            tick=low+left
            values.append(date.fromordinal(tick).isoformat() if kind=='date' else
                          Decimal(tick).scaleb(-field['places']) if kind=='decimal' else tick)
        return values
    if kind=='normal':
        output=[]
        for _ in range(count):
            raw=random.gauss(float(field['mean']),float(field['sd']))
            output.append(rounded_normal(raw,field['places']))
        return output
    if kind=='boolean':
        numerator,denominator=Decimal(field['probability']).as_integer_ratio()
        return [random.randrange(denominator)<numerator for _ in range(count)]
    if kind=='date':
        low,high,_=domain(field)
        return [date.fromordinal(random.randint(low,high)).isoformat() for _ in range(count)]
    if kind=='date_sequence':
        start=day(field['start'],'start')
        return [date.fromordinal(start+i*field['step']).isoformat() for i in range(count)]
    if kind=='category_quota':
        counts=quota_counts(document,field,count)
        output=[value for value,total in zip(field['values']+[None],counts) for _ in range(total)]
        random.shuffle(output)
        return output
    return None
