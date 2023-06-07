from flask import Flask, send_file, request
from flask_restful import Api, Resource


from resources.apps.eligibility import EligibilitesManagement
from resources.apps.rule import RulesManagement


import os

directory = 'storage'

# Check if the directory exists
if not os.path.exists(directory):
    # Create the directory
    os.makedirs(directory)
    print(f"Directory '{directory}' created successfully!")
else:
    print(f"Directory '{directory}' already exists.")


app = Flask(__name__)
api = Api(app)

class FileDownloadResource(Resource):
    
    def get(self,):
        filename = request.args.get('filename')
        # Return the file for download
        return send_file(f"storage/{filename}", as_attachment=True)



api.add_resource(EligibilitesManagement, '/filter/eligibility/')
api.add_resource(RulesManagement, '/filter/rules/')

api.add_resource(FileDownloadResource, '/download/')


if __name__ == '__main__':
    app.run(debug=True)