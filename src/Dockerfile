FROM public.ecr.aws/lambda/python:3.13

COPY src/main.py ${LAMBDA_TASK_ROOT}

COPY requirements.txt ./

RUN pip install -r requirements.txt

CMD ["main.lambda_handler"]

