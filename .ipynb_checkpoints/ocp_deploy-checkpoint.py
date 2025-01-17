
%pip install openshift-client
import os
import openshift as oc
from jinja2 import Template
import time
import shutil
run_id = "5"
project = "ai-project"

os.environ['OPENSHIFT_CLIENT_PYTHON_DEFAULT_OC_PATH'] = '/tmp/oc'


model_name = 'educationdemo'
model_version = "1"# os.environ["MODEL_VERSION"]
build_name = f"seldon-model-{model_name}-v{model_version}"
def download_artifacts():
    print("Retrieving model metadata ...")
    #shutil.copy("../../models", "", *, follow_symlinks=True)
    print("Download successful")
    
    return run_id
    
        
run_id = download_artifacts()

print("Start OCP things...")
#print('OpenShift server version: {}'.format(oc.get_server_version()))
token = os.environ["OPENSHIFT_API_LOGIN_TOKEN"]
server = os.environ["OPENSHIFT_API_SERVER"]
print(token)
print(server)




#build from source Docker file
with oc.api_server(server):
    with oc.token(token):
        with oc.project(project), oc.timeout(10*60):
            print('OpenShift client version: {}'.format(oc.get_client_version()))
            #print('OpenShift server version: {}'.format(oc.get_server_version()))

            build_config = oc.selector(f"bc/{build_name}").count_existing() #.object
            print(oc.get_project_name())
            print(build_config)
            if build_config == 0:
                oc.new_build(["--strategy", "docker", "--binary", "--docker-image", "registry.access.redhat.com/ubi8/python-38:1-71", "--name", build_name ])
            else:
                build_details = oc.selector(f"bc/{build_name}").object()
                print(build_details.as_json())
                
            print("Starting Build and Wiating.....")
            build_exec = oc.start_build([build_name, "--from-dir", ".", "--follow", "--build-loglevel", "10"])
            print("Build Finished")
            status = build_exec.status()
            print(status)
            for k, v in oc.selector([f"bc/{build_name}"]).logs(tail=500).items():
                print('Build Log: {}\n{}\n\n'.format(k, v))

            #seldon_deploy = oc.selector(f"SeldonDeployment/{build_name}").count_existing()
            #experiment_id = mlflow.get_run(run_id).info.experiment_id

            template_data = {"experiment_id": run_id, "model_name": model_name, "image_name": build_name, "project": project}
            applied_template = Template(open("service.yaml").read())
            print(applied_template.render(template_data))
            oc.apply(applied_template.render(template_data))
            

            
            route_count = oc.selector(f"route/{build_name}").count_existing()
            print(route_count)
            if route_count == 0:
                service_name = "model-" + run_id + "-" + model_name
                while True:
                    service_count = oc.selector(f"service/{service_name}").count_existing()
                    if service_count > 0:
                        service = oc.selector(f"service/{service_name}").object()
                        print(service.name())
                        oc.oc_action(oc.cur_context(), "expose", cmd_args=["service", service.name(), "--name", service.name()])
                        break
                    else:
                        print(f"Service name does not exist {service_name}")
                        time.sleep(10)
            else:
                print(f"Route already exists {service_name}")


