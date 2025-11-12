# docker-training-app

This is a toy RAG to be used as scaffold for training on `docker` and `docker-compose`.
The project also aims for showing the basic architecture of a basic `chatbot + RAG` solution.

Branch or fork this repository at will to modify it.

## Components

- 💬 `chatbot`: backend service that responds to messages prompted by the user. the communication is featured as a REST API.
- 🎨 `ui`: basic web form for sending messages to the chatbot endpoints interactively.
- 🧠 `llm`: language model used to generate answers based on user inputs and context.
- 🔢 `encoder`: small language model used for generating embeddings from text. this is used both for indexing and querying the vector DB.
- 🗄️ `vector-db`: documents DB with semantic search capabilities.
- ⚒️ `data-indexer`: batch job that chunks a set of documents and loads it into the vector DB.