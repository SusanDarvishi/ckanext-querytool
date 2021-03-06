from ckan.plugins import toolkit

from ckanext.querytool.logic import validators


not_missing = toolkit.get_validator('not_missing')
not_empty = toolkit.get_validator('not_empty')
ignore_missing = toolkit.get_validator('ignore_missing')
package_id_exists = toolkit.get_validator('package_id_exists')
name_validator = toolkit.get_validator('name_validator')
isodate = toolkit.get_validator('isodate')


def querytool_schema():
    return {
        'name': [not_empty,
                 name_validator,
                 validators.querytool_name_validator,
                 unicode],
        'title': [not_empty, unicode],
        'dataset_name': [not_empty, unicode],
        'description': [ignore_missing, unicode],
        'filters': [not_missing, not_empty, unicode],
        'sql_string': [ignore_missing, unicode],
        'created': [ignore_missing, isodate],
        'modified': [ignore_missing, isodate],
        'map_resource': [not_empty, unicode],
        'chart_resource': [not_empty, unicode],
        'y_axis_columns': [not_empty, unicode],
    }
