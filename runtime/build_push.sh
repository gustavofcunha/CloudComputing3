#!/bin/bash

docker build -t gustavofcunha/serverless-runtime:v1 -f Dockerfile .
docker push gustavofcunha/serverless-runtime:v1