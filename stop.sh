#!/bin/bash

for f in k8s/ ;do
	kubectl delete -f "$f"
done
