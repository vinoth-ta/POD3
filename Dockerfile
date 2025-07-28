FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY sttm_to_notebook_generator_integrated/ /app/sttm_to_notebook_generator_integrated/
COPY notebook_generator_app/ /app/notebook_generator_app/
COPY static/ /app/static/
COPY templates/ /app/notebook_generator_app/templates/


EXPOSE 8000

CMD ["uvicorn", "sttm_to_notebook_generator_integrated.api3_sttm_to_notebook_generator:app", "--host", "0.0.0.0", "--port", "8000"]
 