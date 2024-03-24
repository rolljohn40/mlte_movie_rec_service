import requests
import logging

from typing import Optional


def get_user_data(user_id: int) -> Optional[dict]:
    url = f"http://128.2.204.215:8080/user/{user_id}"
    user_data = None
    try:
        response = requests.get(url)
        if response.status_code == 200:
            user_data = response.json()
            assert isinstance(user_data["user_id"], int)
            assert isinstance(user_data["age"], int)
            assert isinstance(user_data["occupation"], str)
            assert isinstance(user_data["gender"], str)
            return user_data
        else:
            logging.error(f"Status {response.status_code} while getting user {user_id}")
        return user_data
    except requests.exceptions.RequestException as e:
        logging.error(f"Error {e} while getting user {user_id}")
        return None
    except AssertionError as e:
        logging.error(f"Iill-formed response for user {user_id}: {user_data}")
        return None
