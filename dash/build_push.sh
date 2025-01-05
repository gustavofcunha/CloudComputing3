#!/bin/bash

docker build -t gustavofcunha/dashboard:v2 -f Dockerfile .
docker push gustavofcunha/dashboard:v2