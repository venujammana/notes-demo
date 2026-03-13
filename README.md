# Flask Notes API with Google Cloud

This repository contains a simple Flask-based notes application with a CI/CD pipeline using Google Cloud services.

## Architecture

*   Source Code:** GitHub (or Cloud Source Repositories if available)
*   **CI/CD:** Cloud Build, Artifact Registry, Cloud Deploy
*   **Hosting:** Cloud Run
*   **Database:** Firestore (Native Mode)
*   **API Management:** API Gateway
*   **Observability:** Cloud Monitoring, Logging, Alerting

## Prerequisites

Before you begin, you need to enable the following Google Cloud services:

*   Cloud Run: `run.googleapis.com`
*   Cloud Build: `cloudbuild.googleapis.com`
*   Artifact Registry: `artifactregistry.googleapis.com`
*   Cloud Deploy: `clouddeploy.googleapis.com`
*   API Gateway: `apigateway.googleapis.com`
*   Identity and Access Management (IAM): `iam.googleapis.com`
*   Firestore: `firestore.googleapis.com`
*   Cloud Logging: `logging.googleapis.com`
*   Cloud Monitoring: `monitoring.googleapis.com`
*   Cloud Resource Manager: `cloudresourcemanager.googleapis.com`

You can enable these services with the following `gcloud` command:

```bash
gcloud services enable \
    run.googleapis.com \
    cloudbuild.googleapis.com \
    artifactregistry.googleapis.com \
    clouddeploy.googleapis.com \
    apigateway.googleapis.com \
    iam.googleapis.com \
    firestore.googleapis.com \
    logging.googleapis.com \
    monitoring.googleapis.com \
    cloudresourcemanager.googleapis.com
```

**Note:** If you don't have access to Cloud Source Repositories, you can use GitHub as your source code repository. This guide will assume you are using GitHub.

## IAM Setup

We will create a dedicated service account for our CI/CD pipeline to ensure secure and granular access to Google Cloud resources.

1.  **Create a service account:**

    ```bash
    gcloud iam service-accounts create notes-sa \
        --description="Service account for notes-demo" \
        --display-name="notes-demo-sa"
    ```

2.  **Grant the required roles to the service account:**

    ```bash
    gcloud projects add-iam-policy-binding $(gcloud config get-value project) \
        --member="serviceAccount:notes-sa@$(gcloud config get-value project).iam.gserviceaccount.com" \
        --role="roles/run.admin"

    gcloud projects add-iam-policy-binding $(gcloud config get-value project) \
        --member="serviceAccount:notes-sa@$(gcloud config get-value project).iam.gserviceaccount.com" \
        --role="roles/iam.serviceAccountUser"

    gcloud projects add-iam-policy-binding $(gcloud config get-value project) \
        --member="serviceAccount:notes-sa@$(gcloud config get-value project).iam.gserviceaccount.com" \
        --role="roles/clouddeploy.jobRunner"

    gcloud projects add-iam-policy-binding $(gcloud config get-value project) \
        --member="serviceAccount:notes-sa@$(gcloud config get-value project).iam.gserviceaccount.com" \
        --role="roles/cloudbuild.builds.editor"

    gcloud projects add-iam-policy-binding $(gcloud config get-value project) \
        --member="serviceAccount:notes-sa@$(gcloud config get-value project).iam.gserviceaccount.com" \
        --role="roles/datastore.user"

    gcloud projects add-iam-policy-binding $(gcloud config get-value project) \
        --member="serviceAccount:notes-sa@$(gcloud config get-value project).iam.gserviceaccount.com" \
        --role="roles/artifactregistry.writer"

    gcloud projects add-iam-policy-binding $(gcloud config get-value project) \
        --member="serviceAccount:notes-sa@$(gcloud config get-value project).iam.gserviceaccount.com" \
        --role="roles/logging.logWriter"

    gcloud projects add-iam-policy-binding $(gcloud config get-value project) \
        --member="serviceAccount:notes-sa@$(gcloud config get-value project).iam.gserviceaccount.com" \
        --role="roles/monitoring.metricWriter"

    gcloud projects add-iam-policy-binding $(gcloud config get-value project) \
        --member="serviceAccount:notes-sa@$(gcloud config get-value project).iam.gserviceaccount.com" \
        --role="roles/apigateway.admin"
    ```

## Firestore Setup

We will use Firestore in Native mode as the database for our notes application.

1.  **Create a Firestore database:**

    Choose a region where Firestore is available (e.g., `us-central`).

    ```bash
    gcloud firestore databases create --location=us-central
    ```

    **Note:** This operation is permanent and cannot be undone. You must have the appropriate permissions to create a Firestore database. If you encounter a permission error, please ensure your account has the `datastore.owner` or `datastore.user` role.

## CI/CD Pipeline

We will use Cloud Build to automatically build and deploy our application. This pipeline is configured to use your Git repository for version control (e.g., GitHub). Each build will produce a Docker image tagged with the commit SHA, ensuring proper versioning.

1.  **Create an Artifact Registry repository:**

    ```bash
    gcloud artifacts repositories create notes-repo \
        --repository-format=docker \
        --location=us-central1 \
        --description="Docker repository for notes-demo"
    ```

2.  **Connect your GitHub repository to Cloud Build:**

    *   Go to the Cloud Build triggers page in the Google Cloud Console.
    *   Click "Connect repository".
    *   Select "GitHub" as the source.
    *   Authenticate and select your repository.
    *   Click "Connect repository".

3.  **Create a Cloud Build trigger:**

    *   Go to the Cloud Build triggers page.
    *   Click "Create trigger".
    *   **Name:** `deploy-to-run`
    *   **Event:** Push to a branch
    *   **Source repository:** Select your repository
    *   **Branch:** `^main$`
    *   **Configuration:** Cloud Build configuration file (yaml or json)
    *   **Cloud Build configuration file location:** `cloudbuild.yaml`
    *   Click "Create".

Now, whenever you push a change to the `main` branch of your GitHub repository, a new build will be triggered. Cloud Build will build your application, identified by its unique commit SHA, and then directly deploy it to Cloud Run using `gcloud run deploy`.

## Cloud Deploy Pipeline

We will use Cloud Deploy to create a delivery pipeline that will deploy our application to `dev`, `staging`, and `prod` environments.

1.  **Create the Cloud Deploy pipeline:**

    ```bash
    gcloud deploy apply --file=clouddeploy.yaml --region=us-central1 --project=$(gcloud config get-value project)
    ```

    This command will create the delivery pipeline and the targets defined in the `clouddeploy.yaml` file.

## API Gateway

We will use API Gateway to expose our Cloud Run service to the internet.

1.  **Update the `openapi.yaml` file:**

    Before creating the API Gateway, you need to update the `openapi.yaml` file. The `x-google-backend.address` field uses a placeholder `NOTES_APP_PROD_URL`. You must provide this as a substitution variable when triggering the build, setting its value to the URL of your `notes-app-prod` Cloud Run service. You can get the URL from the Cloud Run page in the Google Cloud Console.

2.  **Create an API:**

    ```bash
    gcloud api-gateway apis create notes-api --project=$(gcloud config get-value project)
    ```

3.  **Create an API config:**

    ```bash
    gcloud api-gateway api-configs create notes-api-config \
      --api=notes-api --openapi-spec=openapi.yaml \
      --project=$(gcloud config get-value project) \
      --backend-auth-service-account=notes-sa@$(gcloud config get-value project).iam.gserviceaccount.com
    ```

4.  **Create a gateway:**

    ```bash
    gcloud api-gateway gateways create notes-gateway \
      --api=notes-api --api-config=notes-api-config \
      --location=us-central1 --project=$(gcloud config get-value project)
    ```

    This will give you a URL for your API Gateway.

## Monitoring, Logging, and Alerting

We will set up basic monitoring, logging, and alerting using Google Cloud's operations suite.

1.  **Cloud Logging:**
    All logs from your Cloud Run service and API Gateway will automatically be sent to Cloud Logging. You can view these logs in the Logs Explorer.

2.  **Create a Log-based Metric for Errors:**
    *   Go to **Logging** > **Logs Explorer**.
    *   Filter for errors from your Cloud Run service (e.g., `resource.type="cloud_run_revision" AND severity=ERROR`).
    *   Click "Create metric" at the top right.
    *   **Metric name:** `notes-app-error-count`
    *   Click "Create metric".

3.  **Create an Alerting Policy:**
    *   Go to **Monitoring** > **Alerting**.
    *   Click "Create policy".
    *   **Condition:** Select the `notes-app-error-count` metric. Configure it to alert if the count is greater than 0 for a 5-minute period.
    *   **Notification Channels:** Configure your preferred notification channels (email, PagerDuty, etc.).
    *   **Name:** `Notes App Error Alert`
    *   Click "Create policy".

4.  **Create a Custom Dashboard (Optional but Recommended):**
    *   Go to **Monitoring** > **Dashboards**.
    *   Click "Create dashboard".
    *   Add charts to visualize key metrics, such as:
        *   Cloud Run request count and latency.
        *   API Gateway request count and errors.
        *   `notes-app-error-count` log-based metric.

## Local Development

To run the application locally, follow these steps:

1.  **Create and activate a Python virtual environment:**

    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

2.  **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

3.  **Set up Google Application Credentials:**

    If you want to interact with Firestore locally, you need to set the `GOOGLE_APPLICATION_CREDENTIALS` environment variable.

    *   Create a service account key in JSON format from the Google Cloud Console (IAM & Admin -> Service Accounts -> Create Service Account -> Create Key).
    *   Download the JSON key file.
    *   Set the environment variable:

        ```bash
        export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/keyfile.json"
        ```

4.  **Run the Flask application:**

    ```bash
    python3 main.py
    ```

    The application will be accessible at `http://127.0.0.1:8080`.

## Clean Up

To avoid incurring unnecessary charges, you can delete all the Google Cloud resources created by this project.

1.  **Delete the API Gateway:**

    ```bash
    gcloud api-gateway gateways delete notes-gateway --location=us-central1 --project=$(gcloud config get-value project)
    gcloud api-gateway api-configs delete notes-api-config --api=notes-api --project=$(gcloud config get-value project)
    gcloud api-gateway apis delete notes-api --project=$(gcloud config get-value project)
    ```

2.  **Delete the Cloud Run services:**

    ```bash
    gcloud run services delete notes-app-dev --region=us-central1 --project=$(gcloud config get-value project)
    gcloud run services delete notes-app-staging --region=us-central1 --project=$(gcloud config get-value project)
    gcloud run services delete notes-app-prod --region=us-central1 --project=$(gcloud config get-value project)
    ```

3.  **Delete the Cloud Deploy pipeline and targets:**

    ```bash
    gcloud deploy delivery-pipelines delete notes-pipeline --region=us-central1 --project=$(gcloud config get-value project)
    gcloud deploy targets delete dev --region=us-central1 --project=$(gcloud config get-value project)
    gcloud deploy targets delete staging --region=us-central1 --project=$(gcloud config get-value project)
    gcloud deploy targets delete prod --region=us-central1 --project=$(gcloud config get-value project)
    ```

4.  **Delete the Artifact Registry repository:**

    ```bash
    gcloud artifacts repositories delete notes-repo --location=us-central1 --project=$(gcloud config get-value project)
    ```

5.  **Delete the Service Account:**

    ```bash
    gcloud iam service-accounts delete notes-sa@$(gcloud config get-value project).iam.gserviceaccount.com --project=$(gcloud config get-value project)
    ```

6.  **Delete the Firestore database:**

    Deleting a Firestore database is not directly possible via `gcloud` CLI. You will have to do it manually from the Google Cloud Console or use `gcloud alpha firestore databases delete` if available and enabled.

    *   Go to **Firestore** in the Google Cloud Console.
    *   Select your database and delete it.

## Endpoints

*   `GET /health`: Health check endpoint.
*   `GET /notes`: Retrieves all notes from Firestore.
*   `POST /notes`: Creates a new note in Firestore.
