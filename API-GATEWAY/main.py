from fastapi import FastAPI, HTTPException, Depends, Request, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from typing import List, Optional
import jwt
import httpx
import bcrypt
from datetime import datetime

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Use this function to get the current user (requires authentication)
async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        print("Extracted Token:", token)
        payload = jwt.decode(token, 'your-secret-key', algorithms=['HS256'])
        return {'token': token, **payload}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail='Token has expired')
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail='Invalid token')


@app.middleware("http")
async def add_custom_header(request: Request, call_next):
    response = await call_next(request)
    response.headers["Custom-Header"] = "Custom-Value"
    return response

# Assuming you have the user and post services running on different ports
USER_SERVICE_URL = "http://localhost:3001"  # Replace with your actual user service URL
POST_SERVICE_URL = "http://localhost:3002"  # Replace with your actual post service URL

# Pydantic model for User registration
class UserRegister(BaseModel):
    name: str
    username: str
    email: str
    password: str

# Pydantic model for User response
class UserResponse(BaseModel):
    user_id: str
    name: str
    username: str
    email: str

# Pydantic model for User login with email or username
class UserLogin(BaseModel):
    email_or_username: str
    password: str

# Pydantic model for Post creation
class PostCreate(BaseModel):
    user_id: str
    text: str
    images: list = []
    timestamp: Optional[str] = None  # Add timestamp field

# Pydantic model for Post response
class PostResponse(BaseModel):
    post_id: str
    user_id: str
    text: str
    images: list
    likes: list
    comments: list
    timestamp: str

# User Service Router
user_router = APIRouter()

@user_router.post("/register")
async def register_user(user_data: UserRegister):
    try:
        # Hash the user password before sending it to the User Service
        hashed_password = user_data.password
        # user_data.password = hashed_password  # Convert bytes to string
        user_service_response = httpx.post(f"{USER_SERVICE_URL}/register", json=user_data.dict())
        return user_service_response.json()
    except Exception as e:
        print('Error during user registration:', e)
        raise HTTPException(status_code=500, detail='Internal Server Error')

@user_router.post("/login")
async def login_user(user_data: UserLogin):
    try:
        user_service_response = httpx.post(f"{USER_SERVICE_URL}/login", json=user_data.dict())
       
        user_service_data = user_service_response.json()
        print("RESPUESTA" + str(user_service_data))
        print(user_data.dict())  # Log or print the request payload

        # Check if the response status code is 200 and 'token' is present
        if user_service_response.status_code == 200 and 'token' in user_service_data:
            # Extract the token and return it
            return {'token': user_service_data['token'] , 'user': user_service_data['user']}
        else:
            # If the response status code is not 200 or 'token' is not present, handle the error
            raise HTTPException(status_code=user_service_response.status_code, detail='Invalid credentials')
    except httpx.HTTPError as e:
        print('Error during user login:', e)
        raise HTTPException(status_code=e.response.status_code, detail='User Service Error')
    except Exception as e:
        print('Unknown error during user login:', e)
        raise HTTPException(status_code=500, detail='Internal Server Error')

@user_router.get("/profile")
async def view_profile(current_user: dict = Depends(get_current_user)):
    try:
        user_service_response = httpx.get(
            f"{USER_SERVICE_URL}/profile",
            headers={"Authorization": f"Bearer {current_user['token']}"}
        )
        return user_service_response.json()
    except Exception as e:
        print('Error during fetching profile:', e)
        raise HTTPException(status_code=500, detail='Internal Server Error')

@user_router.put("/edit_profile")
async def edit_profile(profile_data: dict, current_user: dict = Depends(get_current_user)):
    try:
        user_service_response = httpx.put(
            f"{USER_SERVICE_URL}/edit_profile",
            json=profile_data,
            headers={"Authorization": f"Bearer {current_user['token']}"}
        )
        return user_service_response.json()
    except Exception as e:
        print('Error during profile editing:', e)
        raise HTTPException(status_code=500, detail='Internal Server Error')


@user_router.get("/users/username/{username}", response_model=UserResponse, tags=["user"])
async def get_user_by_username(username: str):
    try:
        print("PRUEBA: " + username)
        user_service_response = httpx.get(f"{USER_SERVICE_URL}/users/username/{username}")
        if user_service_response.status_code == 404:
            raise HTTPException(status_code=404, detail='User not found')
        user_data = user_service_response.json()
        return UserResponse (
            user_id=user_data.get('user_id', None),
            name=user_data.get('name', None),
            username=user_data.get('username', None),
            email=user_data.get('email', None)
        )
        #return user_data;
    except Exception as e:
        print('Error during fetching user by username:', e)
        raise HTTPException(status_code=500, detail='Internal Server Error')
        
@user_router.get("/users/id/{user_id}", response_model=UserResponse, tags=["user"])
async def get_user_by_id(user_id: str):
    try:
        user_service_response = httpx.get(f"{USER_SERVICE_URL}/users/id/{user_id}")
        return user_service_response.json()
    except Exception as e:
        print('Error during fetching user by ID:', e)
        raise HTTPException(status_code=500, detail='Internal Server Error')


@user_router.get("/users", response_model=List[UserResponse], tags=["user"])
async def get_all_users():
    try:
        user_service_response = httpx.get(f"{USER_SERVICE_URL}/users")
        return user_service_response.json()
    except Exception as e:
        print('Error during fetching users:', e)
        raise HTTPException(status_code=500, detail='Internal Server Error')
    
    

# Include the routers in the main app
app.include_router(user_router, prefix="/user", tags=["user"])

# Post Service Router
post_router = APIRouter()

@post_router.get("/feed", response_model=List[PostResponse], tags=["post"])
async def get_feed(request: Request):
    try:
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        print("Current User Token:", token)
        post_service_response = httpx.get(
            f"{POST_SERVICE_URL}/posts",
            headers={"Authorization": f"Bearer {token}"}
        )
        fetched_posts = post_service_response.json()
        print("Received posts from post_service:", fetched_posts)
        return fetched_posts
    except Exception as e:
        print('Error during fetching feed:', e)
        raise HTTPException(status_code=500, detail='Internal Server Error')
    


@post_router.get("/user/{username}", response_model=List[PostResponse], tags=["post"])
async def get_user_posts_by_username(username: str, current_user: dict = Depends(get_current_user)):
    try:
        user_service_response = httpx.get(f"{USER_SERVICE_URL}/users/username/{username}")
        if user_service_response.status_code == 404:
            raise HTTPException(status_code=404, detail='User not found')

        user_data = user_service_response.json()
        user_id = user_data.get('username', None)  # Use the correct field for user_id

        # Debugging: Print current_user information
        print("Current User:", current_user)
        print("Current User Token:", current_user.get('token', 'Token not found'))

        # Fetch posts for the user from the Post Service
        post_service_response = httpx.get(
            f"{POST_SERVICE_URL}/posts/user/{user_id}",
            headers={"Authorization": f"Bearer {current_user['token']}"}  # Pass the correct token
        )

        return post_service_response.json()
    except Exception as e:
        print('Error during fetching user posts by username:', e)
        raise HTTPException(status_code=500, detail='Internal Server Error')




@post_router.post("/create_post")
async def create_post(post_data: PostCreate, current_user: dict = Depends(get_current_user)):
    try:
        # Remove the line below, as we don't need to hash the user_id anymore
        # post_data.user_id = bcrypt.hashpw(current_user['token'].encode(), bcrypt.gensalt())

        post_data.timestamp = str(datetime.utcnow())  # Set the timestamp to the current UTC time
        post_service_response = httpx.post(
            f"{POST_SERVICE_URL}/posts",
            json=post_data.dict(),
            headers={"Authorization": f"Bearer {current_user['token']}"}
        )

        return post_service_response.json()
    except Exception as e:
        print('Error during post creation:', e)
        raise HTTPException(status_code=500, detail='Internal Server Error')



@post_router.get("/post/{post_id}", response_model=PostResponse, tags=["post"])
async def get_post(post_id: str, current_user: dict = Depends(get_current_user)):
    try:
        post_service_response = httpx.get(
            f"{POST_SERVICE_URL}/posts/{post_id}",
            headers={"Authorization": f"Bearer {current_user['token']}"}
        )
        return post_service_response.json()
    except Exception as e:
        print('Error during fetching post:', e)
        raise HTTPException(status_code=500, detail='Internal Server Error')

@post_router.put("/post/{post_id}/like", response_model=PostResponse, tags=["post"])
async def update_post(post_id: str, current_user: dict = Depends(get_current_user)):
    try:
        # Check if the user has already liked the post
        liked_response = httpx.get(
            f"{POST_SERVICE_URL}/posts/post/{post_id}/liked",
            json={'user_id': str(current_user['user_id'])},
            headers={"Authorization": f"Bearer {current_user['token']}"}
        )
        is_liked = liked_response.json().get('liked', False)

        if is_liked:
            # If already liked, send a request to unlike the post
            post_service_response = httpx.put(
                f"{POST_SERVICE_URL}/posts/post/{post_id}/unlike",
                json={'user_id': str(current_user['user_id'])},
                headers={"Authorization": f"Bearer {current_user['token']}"}
            )
        else:
            # If not liked, send a request to like the post
            post_service_response = httpx.put(
                f"{POST_SERVICE_URL}/posts/post/{post_id}/like",
                json={'user_id': str(current_user['user_id'])},
                headers={"Authorization": f"Bearer {current_user['token']}"}
            )

        return post_service_response.json()
    except Exception as e:
        print('Error during updating post:', e)
        raise HTTPException(status_code=500, detail='Internal Server Error')




@post_router.delete("/post/{post_id}", response_model=dict, tags=["post"])
async def delete_post(post_id: str, current_user: dict = Depends(get_current_user)):
    try:
        post_service_response = httpx.delete(
            f"{POST_SERVICE_URL}/posts/{post_id}",
            headers={"Authorization": f"Bearer {current_user['token']}"}
        )
        return post_service_response.json()
    except Exception as e:
        print('Error during deleting post:', e)
        raise HTTPException(status_code=500, detail='Internal Server Error')
    

# Include the post router in the main app
app.include_router(post_router, prefix="/post", tags=["post"])

# Run the FastAPI application using UVicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000)