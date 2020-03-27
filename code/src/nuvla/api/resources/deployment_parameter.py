
class DeploymentParameter(object):

    CURRENT_DESIRED = {'name': 'current.desired.state',
                       'description': "Desired state of the container's current task."}

    CURRENT_STATE = {'name': 'current.state',
                     'description': "Actual state of the container's current task."}

    CURRENT_ERROR = {'name': 'current.error.message',
                     'description': "Error message (if any) of the container's current task."}

    REPLICAS_DESIRED = {'name': 'replicas.desired',
                        'description': 'Desired number of service replicas.'}

    REPLICAS_RUNNING = {'name': 'replicas.running',
                        'description': 'Number of running service replicas.'}

    CHECK_TIMESTAMP = {'name': 'check.timestamp',
                       'description': 'Service check timestamp.'}

    RESTART_NUMBER = {'name': 'restart.number',
                      'description': 'Total number of restarts of all containers due to failures.'}

    RESTART_ERR_MSG = {'name': 'restart.error.message',
                       'description': 'Error message of the last restarted container.'}

    RESTART_EXIT_CODE = {'name': 'restart.exit.code',
                         'description': 'Exit code of the last restarted container.'}

    RESTART_TIMESTAMP = {'name': 'restart.timestamp',
                         'description': 'Restart timestamp of the last restarted container.'}

    SERVICE_ID = {'name': 'service-id',
                  'description': 'Service ID.'}

    HOSTNAME = {'name': 'hostname',
                'description': 'Hostname or IP to access the service.'}
