class ResourceNotFound(Exception):
    pass


class ResourceCreateError(Exception):
    def __init__(self, reason, response=None):
        super(ResourceCreateError, self).__init__(reason)
        self.reason = reason
        self.response = response


def check_created(resp, errmsg=''):
    """
    Returns id of the created resource or raises ResourceCreateError.
    :param resp: nuvla.api.models.CimiResponse
    :param errmsg: error message
    :return: str, resource id
    """
    if resp.data['status'] == 201:
        return resp.data['resource-id']
    else:
        if errmsg:
            msg = '{0} : {1}'.format(errmsg, resp.data['message'])
        else:
            msg = resp.data['message']
        raise ResourceCreateError(msg, resp)


