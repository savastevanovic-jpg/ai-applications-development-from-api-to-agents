import json

from langchain_huggingface import HuggingFaceEmbeddings


class EmbeddingsClient:
    _endpoint: str
    _api_key: str

    def __init__(self, endpoint: str, model_name: str, api_key: str):
        self._model_name = model_name
        self._embeding_clinet = HuggingFaceEmbeddings(
            model_name=model_name,
        )

    def get_embeddings(
            self, inputs: str | list[str],
            dimensions: int,
            print_response: bool = False
    ) -> dict[int, list[float]]:
        """
        Generate dict of indexed embeddings:
            inputs[0](text) -> [0][embedding]
            inputs[1](text) -> [1][embedding]
            ...

        Args:
            inputs: input text, can be singular string or list of strings
            dimensions: number of dimensions
            print_response: to print response in chat or not
        """
        #TODO:
        # Provide implementation that will generate embeddings for `inputs` list (don't forget about dimensions) with
        # Embedding model and return back a dict with indexed embeddings (key is index from input list and value vector list)
        embeddings = self._embeding_clinet.embed_documents(inputs if isinstance(inputs, list) else [inputs])
        indexed_embeddings = {i: embedding[:dimensions] for i, embedding in enumerate(embeddings)}
        if print_response:
            print(json.dumps(indexed_embeddings, indent=2))
        return indexed_embeddings



