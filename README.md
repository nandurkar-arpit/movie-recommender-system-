# Movie Recommender System

A movie recommendation web application built with **Streamlit** for the
user interface and **FastAPI** for the backend API. The project uses
movie metadata and preprocessed files to generate movie recommendations.

## Features

-   Search for a movie through the Streamlit interface.
-   Get movie recommendations through the FastAPI backend.
-   Interactive web interface built with Streamlit.
-   API endpoints available through FastAPI's automatic Swagger
    documentation.

> The exact recommendation method and API routes depend on the
> implementation in `main.py` and `app.py`.

## Project Structure

``` text
movie-recommender-system/
├── .env                    # Local environment variables (do not commit)
├── app.py                  # Streamlit frontend
├── main.py                 # FastAPI backend
├── movie_recommend.ipynb   # Jupyter notebook used during development
├── movies_metadata.csv     # Movie metadata dataset
├── df.pkl                  # Serialized dataframe
├── indices.pkl             # Serialized movie indices
├── tfidf.pkl               # Serialized TF-IDF vectorizer
├── tfidf_matrix.pkl        # Serialized TF-IDF matrix
└── requirements.txt        # Python dependencies
```

## Tech Stack

-   Python
-   Streamlit
-   FastAPI
-   Uvicorn
-   Pandas / NumPy / scikit-learn (if listed in `requirements.txt`)
-   Pickle files for saved, preprocessed objects

## Run Locally

### 1. Clone the repository

``` bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd movie-recommender-system
```

Replace `<YOUR_GITHUB_REPOSITORY_URL>` with your repository's clone URL.

### 2. Create and activate a virtual environment (recommended)

**Windows:**

``` bash
python -m venv venv
venv\Scripts\activate
```

**macOS / Linux:**

``` bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

``` bash
pip install -r requirements.txt
```

### 4. Configure environment variables

If the application requires environment variables, create a local `.env`
file and add the required values. Do not upload `.env` or secrets to
GitHub.

### 5. Start the FastAPI backend

From the project directory, run:

``` bash
uvicorn main:app --reload
```

The API will usually be available at:

``` text
http://127.0.0.1:8000
```

Open the interactive API documentation at:

``` text
http://127.0.0.1:8000/docs
```

### 6. Start the Streamlit frontend

Open a second terminal, activate the same virtual environment, and run:

``` bash
streamlit run app.py
```

Streamlit will print the local address for the app (commonly
`http://localhost:8501`). Make sure `app.py` is configured to send
requests to the running FastAPI backend.

## Deployment

The frontend and backend can be deployed separately:

-   **FastAPI backend:** deploy `main.py` to a Python web-service host.
    A typical start command is:

    ``` bash
    uvicorn main:app --host 0.0.0.0 --port $PORT
    ```

-   **Streamlit frontend:** deploy `app.py` using Streamlit Community
    Cloud, selecting this repository and `app.py` as the main file.

After deploying the backend, configure the frontend to use the deployed
API base URL instead of the local address. Add any required environment
variables through the hosting platform's settings.

Deployment commands and configuration may need adjustment based on the
hosting provider and the code in this repository.

## Data and Model Files

The repository includes a CSV dataset and serialized `.pkl` files used
by the application. Keep the files in the locations expected by the
code. Pickle files should only be loaded from trusted sources.

If the dataset or model files are too large for GitHub, consider using
Git LFS or a suitable model/data hosting service, and update the
application to retrieve them as needed.

## Notes

-   Run the FastAPI backend and Streamlit frontend in separate terminals
    when testing locally.
-   Ensure the API URL configured in `app.py` matches the backend
    address.
-   Do not commit `.env`, API keys, passwords, or other secrets. Add
    `.env` to `.gitignore`.

## License

Add a license here if you intend to make this project open source.
