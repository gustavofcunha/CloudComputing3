#!/bin/bash

docker build -t gustavofcunha/dashboard:v1 -f Dockerfile .
docker push gustavofcunha/dashboard:v1