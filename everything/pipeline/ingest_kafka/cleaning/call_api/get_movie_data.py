import requests
import logging

def get_movie_details(movie_id):
    # Construct the API URL with the movie ID
    url = f"http://128.2.204.215:8080/movie/{movie_id}"
    
    try:
        # Send a GET request to the API
        response = requests.get(url)

        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            # Parse the JSON response
            movie_data = response.json()

            # Extract relevant information
            movie_details = {
                "id": movie_data["id"],
                "tmdb_id": movie_data["tmdb_id"],
                "imdb_id": movie_data["imdb_id"],
                "adult": movie_data["adult"],
                "genres": [genre["name"] for genre in movie_data["genres"]],
                "original_language": movie_data["original_language"],
                "popularity": movie_data["popularity"],
                "runtime": movie_data["runtime"],
                "vote_average": movie_data["vote_average"],
                "vote_count": movie_data["vote_count"],
            }

            return movie_details
        else:
            logging.error(f"Failed to fetch movie {movie_id}. Status code: {response.status_code}")
            return None
    except requests.RequestException as e:
        logging.error(f"Error fetching movie details: {e}")
        return None