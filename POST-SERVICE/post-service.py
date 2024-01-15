from xml.dom import ValidationErr
from fastapi import FastAPI, HTTPException, Depends, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from pymongo import MongoClient
from bson import ObjectId
from pydantic import BaseModel
import jwt
from datetime import datetime
from typing import List, Optional
import uvicorn
###from Users/samuelmartin/Desktop/PROTOTIPO/API-GATEWAY/main import get_current_user



oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        print("Extracted Token:", token)
        payload = jwt.decode(token, 'your-secret-key', algorithms=['HS256'])
        return {'token': token, **payload}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail='Token has expired')
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail='Invalid token')
    
app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Replace with your actual MongoDB connection string
client = MongoClient('mongodb+srv://admin:admin@cluster0.wssor6b.mongodb.net')
db = client['socialweb']
post_collection = db['posts']

# Pydantic model for Post creation
class PostCreate(BaseModel):
    user_id: str
    text: str
    images: list = []
    likes: list = []
    comments: list = []

# Pydantic model for Post response
class PostResponse(BaseModel):
    post_id: str
    user_id: str
    timestamp: str
    text: str
    images: list
    likes: list
    comments: list

# Handle post creation
# Handle post creation
@app.post('/posts', response_model=PostResponse)
async def create_post(post_data: PostCreate):
    try:
        post = {
            'user_id': post_data.user_id,
            'timestamp': datetime.utcnow().isoformat(),
            'text': post_data.text,
            'images': post_data.images,
            'likes': post_data.likes,
            'comments': post_data.comments,
        }
        print("************************")
        print("Aqui vaA-->" + str(post))
        print("************************")
    
        result = post_collection.insert_one(post)
        created_post = post_collection.find_one({'_id': result.inserted_id})

        response_data = {
            'post_id': str(result.inserted_id),  # Use result.inserted_id directly
            'user_id': post_data.user_id,
            'text': post_data.text,
            'images': post_data.images,
            'likes': [],
            'comments': [],
            'timestamp': str(datetime.utcnow())
        }
        return response_data  # Return the dictionary directly, not inside another dictionary
    except ValidationErr as e:
        print('Validation error during post creation:', e)
        raise HTTPException(status_code=422, detail='Unprocessable Entity: Validation Error')
    except Exception as e:
        print('Error during post creation:', e)
        raise HTTPException(status_code=500, detail='Internal Server Error: Failed to create post')




@app.get('/posts', response_model=List[PostResponse])
async def get_all_posts():
    try:
        posts = list(post_collection.find())
        formatted_posts = []

        for post in posts:
            formatted_post = {
                'post_id': str(post['_id']),
                'user_id': post['user_id'],
                'timestamp': str(post.get('timestamp', '')),  # Convert to string with default value
                'text': post.get('text', ''),  # Add similar lines for other fields with default values
                'images': post.get('images', []),
                'likes': post.get('likes', []),
                'comments': post.get('comments', []),
            }
            formatted_posts.append(formatted_post)

        print("Fetched posts:", formatted_posts)
        return formatted_posts
    except Exception as e:
        print('Error during fetching posts:', e)
        raise HTTPException(status_code=500, detail='Internal Server Error')


# Retrieve and return a specific post
@app.get('/posts/{post_id}', response_model=PostResponse)
async def get_post(post_id: str):
    try:
        post = post_collection.find_one({'_id': ObjectId(post_id)})

        if post:
            return {
                'post_id': str(post['_id']),
                'user_id': post['user_id'],
                'timestamp': post['timestamp'],
                'text': post['text'],
                'images': post['images'],
                'likes': post['likes'],
                'comments': post['comments'],
            }
        else:
            raise HTTPException(status_code=404, detail='Post not found')
    except Exception as e:
        print('Error during fetching a post:', e)
        raise HTTPException(status_code=500, detail='Internal Server Error')

# Update a specific post
@app.put('/posts/{post_id}', response_model=PostResponse)
async def update_post(post_id: str, post_data: PostCreate):
    try:
        updated_post = {
            'user_id': post_data.user_id,
            'timestamp': datetime.utcnow().isoformat(),
            'text': post_data.text,
            'images': post_data.images,
            'likes': post_data.likes,
            'comments': post_data.comments
        }

        result = post_collection.update_one({'_id': ObjectId(post_id)}, {'$set': updated_post})

        if result.modified_count == 1:
            # Retrieve the updated post to include likes and comments
            updated_post = post_collection.find_one({'_id': ObjectId(post_id)})
            return {
                'post_id': post_id,
                'user_id': post_data.user_id,
                'timestamp': updated_post['timestamp'],
                'text': post_data.text,
                'images': post_data.images,
                'likes': updated_post['likes'],
                'comments': updated_post['comments'],
            }
        else:
            raise HTTPException(status_code=404, detail='Post not found')
    except Exception as e:
        print('Error during updating a post:', e)
        raise HTTPException(status_code=500, detail='Internal Server Error')
    

# Delete a specific post
@app.delete('/posts/{post_id}', response_model=dict)
async def delete_post(post_id: str):
    try:
        result = post_collection.delete_one({'_id': ObjectId(post_id)})

        if result.deleted_count == 1:
            return {"message": "Post successfully deleted"}
        else:
            raise HTTPException(status_code=404, detail='Post not found')
    except Exception as e:
        print('Error during deleting a post:', e)
        raise HTTPException(status_code=500, detail='Internal Server Error')

# Add a new endpoint to the Post Service
@app.get('/posts/user/{user_id}', response_model=List[PostResponse])
async def get_posts_by_user(user_id: str):
    try:
        posts = list(post_collection.find({'user_id': user_id}))
        formatted_posts = []

        for post in posts:
            formatted_post = {
                'post_id': str(post['_id']),
                'user_id': post['user_id'],
                'timestamp': str(post.get('timestamp', '')),  # Convert to string with default value
                'text': post.get('text', ''),
                'images': post.get('images', []),
                'likes': post.get('likes', []),
                'comments': post.get('comments', []),
            }
            formatted_posts.append(formatted_post)

        return formatted_posts
    except Exception as e:
        print('Error during fetching posts by user ID:', e)
        raise HTTPException(status_code=500, detail='Internal Server Error')
    
    


# Add a new endpoint to handle post likes
@app.post('/posts/post/{post_id}/like', response_model=PostResponse)
async def like_post(post_id: str, data: dict = Body(...), current_user: dict = Depends(get_current_user)):
    try:
        user_id = current_user.get('user_id')
        result = post_collection.update_one(
            {'_id': ObjectId(post_id)},
            {'$addToSet': {'likes': user_id}},
        )

        if result.modified_count == 1:
            updated_post = post_collection.find_one({'_id': ObjectId(post_id)})
            return {
                'post_id': post_id,
                'user_id': updated_post['user_id'],
                'timestamp': updated_post['timestamp'],
                'text': updated_post['text'],
                'images': updated_post['images'],
                'likes': updated_post['likes'],
                'comments': updated_post['comments'],
            }
        else:
            raise HTTPException(status_code=404, detail='Post not found')
    except Exception as e:
        print('Error during liking a post:', e)
        raise HTTPException(status_code=500, detail='Internal Server Error')




    




# Run the FastAPI application using UVicorn
if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=3002)