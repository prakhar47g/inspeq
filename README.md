# KServe Model Deployment Guide

## Table of Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Environment Setup](#environment-setup)
- [Deployment](#deployment)
- [Testing](#testing)
- [API Documentation](#api-documentation)
- [Troubleshooting](#troubleshooting)

## Overview
This repository contains implementation and documentation for deploying machine learning models using KServe on Kubernetes. The solution demonstrates enterprise-grade model serving capabilities using a Hugging Face classification model.

## Environment Setup
1. **Kubernetes Cluster Setup**

    Cluster config used:
    - 3 nodes (with auto-scaling)

    Node config:
    - 4 CPU
    - 8GB RAM
    - 160GB storage

    Note: Ensure that cluster should have minimum resources as specified [here](https://knative.dev/docs/install/yaml-install/serving/install-serving-with-yaml/#prerequisites) for KNative and also sufficient overhead for Istio, Kserve and model deployments

2. **KServe Installation**

    Kserve installed in Serverless mode as per the instructions [here](https://kserve.github.io/website/master/admin/serverless/serverless/)

    ```bash
    # Install KNative
    kubectl apply -f https://github.com/knative/serving/releases/download/knative-v1.16.0/serving-crds.yaml
    kubectl apply -f https://github.com/knative/serving/releases/download/knative-v1.16.0/serving-core.yaml

    # Install Istio
    kubectl apply -l knative.dev/crd-install=true -f https://github.com/knative/net-istio/releases/download/knative-v1.16.0/istio.yaml
    kubectl apply -f https://github.com/knative/net-istio/releases/download/knative-v1.16.0/istio.yaml

    kubectl apply -f https://github.com/knative/net-istio/releases/download/knative-v1.16.0/net-istio.yaml

    kubectl get pods -n knative-serving  # Verify that all pods are running
    # Should return soemthing like - 
    # NAME                   READY   UP-TO-DATE   AVAILABLE   AGE
    # activator              1/1     1            1           3d5h
    # autoscaler             1/1     1            1           3d5h
    # controller             1/1     1            1           3d5h
    # net-istio-controller   1/1     1            1           3d5h
    # net-istio-webhook      1/1     1            1           3d5h
    # webhook                1/1     1            1           3d5h

    # Install Cert Manager
    kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.16.2/cert-manager.yaml

    # Install KServe
    helm install kserve-crd oci://ghcr.io/kserve/charts/kserve-crd --version v0.14.1
    helm install kserve oci://ghcr.io/kserve/charts/kserve --version v0.14.1
    ```

    #### Configure DNS

    We can invoke the model using one of the several ways as listed [here](https://kserve.github.io/website/master/get_started/first_isvc/#5-perform-inference), but for the purpose of this project, we will configure routing and port forwarding using sslip.io as listed 
    in [KNative doc](https://knative.dev/docs/install/operator/knative-with-operators/#__tabbed_2_1).

    ```
    kubectl apply -f https://github.com/knative/serving/releases/download/knative-v1.16.0/serving-default-domain.yaml
    ``` 

## Deployment

1. **Deploying a Hugging Face Model from HuggingFace Hub**

    Deploy a model directly from HuggingFace Hub using the provided configuration

    ```bash
    kubectl apply -f deploy/huggingface-distilbert.yaml -n kserve-test
    ```

    This will create an InferenceService in the `kserve-test` namespace that pulls and serves the model from HuggingFace Hub. The following deployments are also done in the `kserve-test` namespace.

    We can get the InferenceService created using 
    ```bash 
    kubectl get inferenceservices -n kserve-test
    # Should return something like 
    # NAME                     URL                                                            READY   PREV   LATEST   PREVROLLEDOUTREVISION   LATESTREADYREVISION                      AGE
    # huggingface-distilbert   http://huggingface-distilbert.kserve-test.139.59.55.131.sslip.io   True           100                              huggingface-distilbert-predictor-00004   2d
    ```
    Here `http://huggingface-distilbert.kserve-test.139.59.55.131.sslip.io` is the url for our deployed service

2. **Deploying a Custom Model using HuggingFace Transformers**

    Deploy a custom model implementation using HuggingFace Transformers framework:

    Building the container is done using the Dockerfile in models/custom-transformers.
    ```bash
    docker buildx build --platform=linux/amd64 -t prakhar11509/inspeq-kserve:amd64 . # ensure that the node architecture is compatible with the container architecture
    ```

    Push the container to a registry
    ```bash
    docker push prakhar11509/inspeq-kserve:amd64
    ```

    Deploy the model    
    ```bash
    kubectl apply -f deploy/custom-transformer.yaml -n kserve-test
    ```

    This will pull the container with your custom model implementation and create an InferenceService to serve predictions.
    As mentioned before, we can get the InferenceService created using 
    ```bash 
    kubectl get inferenceservices -n kserve-test
    ```
   
## Testing
1. Smoke Tests

    - huggingface-distilbert

    ```bash
    curl -v http://huggingface-distilbert.kserve-test.139.59.55.131.sslip.io/v1/models/distilbert:predict \
    -H "content-type: application/json" \
    -d '{"instances": ["Hello, my dog is cute", "I am feeling happy"]}'
    ```

    - custom-transformers
    ```bash
    curl -v -H "Content-Type: application/json" http://kserve-custom-model-logger.kserve-test.139.59.55.131.sslip.io/v1/models/bert-sentiment:predict -d '{"sequence":"hello I am doing good"}'
    ```

2. **Integration Tests**
    Integration tests are implemented using `unittest` framework and can be run using `test_integration_hf.py`. This tests the huggingface-distilbert model.

    ```bash
    # Install dependencies
    pip install -r requirements.txt

    # Run tests
    python -m unittest tests/test_integration_hf.py
    ```

3. **Load Testing**

    Load testing is implemented using `vegeta` tool and can be run using `run_load_test.sh`

    ### Prerequisites
    - Install Vegeta:
    ```bash
    brew install vegeta
    ```

    ### Running Load Tests
    1. The required files are already present in tests/loadtests:
    - `tests/loadtests/target.json`: Contains the API endpoint configuration
    - `tests/loadtests/payload.json`: Contains the test payload
    - `tests/loadtests/run_load_test.sh`: Contains the load test scenarios

    2. Run the load test script from the tests/loadtests directory:
    ```bash
    cd tests/loadtests
    ./run_load_test.sh
    ```

    ### Test Scenarios
    - Constant Load: 10 RPS for 30 seconds
    - Step Load: Gradually increasing from 1 to 20 RPS
    - Spike Test: Sudden burst of 50 RPS for 5 seconds

    ### Results
    Load test results will be generated in the tests/loadtests directory in HTML format:
    - `tests/loadtests/constant_load_plot.html`: Results for constant load test
    - `tests/loadtests/spike_test_plot.html`: Results for spike test


### Model Monitoring

The monitoring setup includes both logging and metrics collection for comprehensive observability of the model serving infrastructure.

#### Monitoring

Models expose metrics in Prometheus format and are scraped using the following stack:

- **Prometheus**: Metrics collection and storage
- **Grafana**: Metrics visualization. Dashboard link: [Grafana](https://prakhar11509.grafana.net/public-dashboards/f00cc56235964ffc854ebc413b1e2803)

#### Logging
Logs are generated by the KServe InferenceService in CloudEvents format and collected using the following stack:

- **CloudEvents**: Structured logging format that provides standardized event metadata
- **Promtail**: Log collector running as DaemonSet in Kubernetes cluster
```bash
# Install Promtail on the cluster
curl -fsS https://raw.githubusercontent.com/grafana/loki/master/tools/promtail.sh | sh -s <Grafana User Id> <Your Grafana.com API Token> <Grafana 
Logs URL> default | kubectl apply --namespace=default -f  -
```

- **Grafana**: Log aggregation system integrated with Grafana Cloud [Logs](https://prakhar11509.grafana.net/a/grafana-lokiexplore-app/explore/
service/kserve-container/logs?patterns=%5B%5D&from=now-15m&to=now&var-ds=grafanacloud-logs&var-filters=service_name%7C%3D%7Ckserve-container&
var-fields=&var-levels=&var-metadata=&var-patterns=&var-lineFilter=&timezone=browser&urlColumns=%5B%5D&visualizationType=%22logs%22&
displayedFields=%5B%5D&sortOrder=%22Descending%22&wrapLogMessage=false)


## API Documentation
API docs are available at [/docs endpoint](http://huggingface-distilbert.kserve-test.139.59.55.131.sslip.io/docs) of the deployed model.
Set it up by adding the following to the InferenceService yaml:
```
apiVersion: serving.kserve.io/v1beta1
kind: InferenceService
metadata:
  name: huggingface-distilbert
  annotations:
    serving.kserve.io/enable-prometheus-scraping: "true"

spec:
  predictor:
    model:
      modelFormat:
        name: huggingface
      protocolVersion: v2
      args:
        - --enable_docs_url=True
# ...
```

## Troubleshooting
- Common issues

1. Pods are in `Pending` state

  - Check if the node has sufficient resources
  - Check if the node has sufficient storage
  - Check if the node has sufficient CPU and memory

2. HuggingFace models deployed using `hf:// storageUri` are not working

This seems like a bug in KServe. The workaround is to use the format as in `deploy/huggingface-distilbert.yaml`

3. Custom model container does not start

Ensure that the container architecture is compatible with the node architecture. e.g. if the node is arm64, the container should be built for arm64.
