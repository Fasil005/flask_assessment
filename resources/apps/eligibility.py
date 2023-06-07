from flask import request
from flask_restful import Resource


from ..utils.filter import EligibilityFilter
from ..utils.response import format_response


class EligibilitesManagement(Resource):

    def post(self, ):
        req = request.get_json()
        try:
            df = EligibilityFilter('ModelCreation.xlsx')
            df.filter(req, list_input=True)
            return format_response(data=df.to_response())

        except Exception as e:
            print(e)
            return format_response(message=e.args, status_code=500)

