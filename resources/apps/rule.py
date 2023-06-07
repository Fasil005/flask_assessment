from flask import request, send_file
from flask_restful import Resource


from ..utils.filter import RuleFilter
from ..utils.response import format_response


class RulesManagement(Resource):

    def post(self, ):
        req = request.get_json()
        try:
            df = RuleFilter('storage/Car loan.xlsx')
            df.filter(req)
            return format_response(data=df.to_response())

        except Exception as e:
            print(e)
            return format_response(message=e.args, status_code=500)


