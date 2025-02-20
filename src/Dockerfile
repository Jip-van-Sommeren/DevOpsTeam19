# Use the AWS Lambda Python 3.8 base image
FROM public.ecr.aws/lambda/python:3.13

COPY main.py ${LAMBDA_TASK_ROOT}
COPY requirements.txt ./

RUN pip install -r requirements.txt

CMD ["main.lambda_handler"]
