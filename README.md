# TOEIC Writing Platform
A simple app to generate topics, submit and evaluate TOEIC Writing essays

## I. Introduction
This is a simple app use AI (through OpenRouter) to automate the generate and evaluate process

## II. Components
|Components|Library / Provider|Note                                   |
|----------|------------------|---------------------------------------|
|Front-end |React             |                                       |
|Back-end  |FastAPI           |                                       |
|AI / Model|OpenRouter        |Use `aiohttp` instead of OpenRouter SDK|


## III. Setup

1. Pull this [repo](https://git.vaito.dev/vair.nooi/ai-toeic)
2. Build the image 
```bash
docker build . -t toeic
```
3. Run the container with the image
```bash
docker run --name toeic --rm -p 5173:5173 -v ~/path/to/data:/app/data -v ~/path/to/.env:/app/.env toeic
```
4. Go to the [web](http://localhost:5173) and use it :D

**Note:** See `.env` file content at [this section](./backend/README.md#ii-enviroment-variables)