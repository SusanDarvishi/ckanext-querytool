# -*- coding: utf-8 -
try:
    # CKAN 2.7 and later
    from ckan.common import config
except ImportError:
    # CKAN 2.6 and earlier
    from pylons import config
import logging
import ckan.model as m
from ckan.common import c
from ckan.plugins import toolkit
import json

log = logging.getLogger(__name__)


def _get_context():
    return {
        'model': m,
        'session': m.Session,
        'user': c.user or c.author,
        'auth_user_obj': c.userobj
    }


def _get_action(action, data_dict):
    return toolkit.get_action(action)(_get_context(), data_dict)


def _get_functions(module_root, functions={}):
    '''
     Helper function that scans extension
     logic/auth dir for all logic/auth functions.
     '''
    for module_name in ['create', 'update', 'delete', 'get']:
        module_path = '%s.%s' % (module_root, module_name,)

        module = __import__(module_path)

        for part in module_path.split('.')[1:]:
            module = getattr(module, part)

        for key, value in module.__dict__.items():
            if not key.startswith('_') \
                    and (hasattr(value, '__call__')
                         and (value.__module__ == module_path)):
                functions[key] = value

    return functions


def user_is_registered(context):
    '''
        Checks if the user is registered user
    '''
    model = context['model']
    user = context['user']
    user_obj = model.User.get(user)
    if not user_obj:
        log.error('User {0} not found').format(user)
        return False

    return True


def get_all_datasets():
    '''
    Get all public datasets
    :return:
    '''
    datasets = _get_action('package_list', {})

    return datasets


def get_filter_values(resource_id, filter_name, previous_filters):
    '''Returns resource field values with no duplicates.'''

    resource = _get_action('resource_show', {'id': resource_id})

    if not resource.get('datastore_active'):
        return []

    data = {
        'resource_id': resource['id'],
        'limit': 0
    }
    result = _get_action('datastore_search', data)

    where_clause = _create_where_clause(previous_filters)

    fields = [field['id'] for field in result.get('fields', [])]
    values = []

    if filter_name in fields:

        sql_string = '''SELECT DISTINCT "{column}"
         FROM "{resource}" {where}'''.format(
            column=filter_name,
            resource=resource_id,
            where=where_clause
        )

        result = _get_action('datastore_search_sql', {'sql': sql_string})
        values = [field[filter_name] for field in result.get('records', [])]

    return sorted(values)


def get_chart_types():
    '''
    Get all avaiable types of chart following c3 specification
    :return:
    '''
    chart_types = [
        {'text': 'Line', 'value': 'line'},
        {'text': 'Bar', 'value': 'bar'},
        {'text': 'Area', 'value': 'area'},
        {'text': 'Spline', 'value': 'spline'},
        {'text': 'Donut', 'value': 'donut'},
        {'text': 'Pie', 'value': 'pie'},
    ]
    return chart_types


def get_color_scheme():
    '''
    Get color schemes for displaying the charts
    :return:
    '''
    colors = [{'value': '#B80000, #995522, #556677, #118888, #115588, '
              '#4C3D3D, #2B2B2B, #660000, #221100',
               'text': 'Saturated'},
              {'value': '#DDBBAA, #79E6F2, #88AA99, #00A864, #228899, '
                        '#3F797F, #775555, #118855, #008751, #3D4C46',
               'text': 'Light'},
              {'value': '#ADC0D8, #79AFF2, #8899AA, #0EAAB2, #00A0A8, '
                        '#776655, #118888, #885511, #3F5C7F, #225599',
               'text': 'Pastel'},
              {'value': '#ADB1D8, #8899AA, #7983F2, #777752, #887711, '
                        '#0070C0, #0062A8, #3F457F, #115588, #3D464C',
               'text': 'Pastel 2'},
              {'value': '#AA9988, #A88600, #779922, #6C7F3F, #887711, '
                        '#555577, #665500, #665100, #4C493D, #2B2B2V',
               'text': 'Contrast'}]

    return colors


def _create_where_clause(filters):

    where_clause = ''

    if any(filters):
        if len(filters) > 1:
            # Loop through filters and create SQL query
            for idx, _ in enumerate(filters):
                op = '='
                name = _['name'].encode('utf-8')
                value = _['value']

                if idx == 0:
                    where_clause = 'WHERE ("{0}" {1} \'{2}\')'.format(
                        name, op, value.encode('utf-8'))
                else:
                    where_clause += ' AND ("{0}" {1} \'{2}\')'.format(
                        name, op, value.encode('utf-8'))

        else:
            _ = filters[0]
            op = '='
            name = _['name'].encode('utf-8')
            value = _['value']
            where_clause = \
                'WHERE ("{0}" {1} \'{2}\')'.format(
                    name,
                    op,
                    value.encode('utf-8')
                )
    return where_clause


def create_query_str(resource_id, filters):

    columns = map(lambda f: '"{0}"'.format(f['name'].encode('utf-8')), filters)
    select = ', '.join(columns)
    where_clause = _create_where_clause(filters)

    # generate the final SQL query string
    sql_string = '''SELECT * FROM "{resource}" {where}'''.format(
        select=select,
        resource=resource_id,
        where=where_clause)

    return sql_string


def get_avaiable_filters(name):

    data_dict = {
        'name': name
    }
    _querytool = _get_action('querytool_get', data_dict)

    filters = json.loads(_querytool['filters'])
    axis_filters = []
    for filter in filters:
        axis_filters.append(filter['name'])

    return axis_filters


def get_dataset_resources(dataset_name):
    dataset_resources = []

    if dataset_name:
        dataset = _get_action('package_show', {'id': dataset_name})

        for res in dataset.get('resources'):
            dataset_resources.append({
                'value': res.get('id'), 'text': res.get('name')
            })

    return dataset_resources


def get_resource_columns(res_id):
    '''

    Get the names of the columns for the resource stored in Datastore

        - res_id: (string) ID of the CKAN resource

    '''

    try:
        res_info = _get_action('datastore_info', {'id': res_id})
    except Exception:
        return []

    fields = res_info.get('schema').keys()

    return fields
