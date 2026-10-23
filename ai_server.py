import io
import torch

from fastapi import FastAPI, UploadFile, File, HTTPException
from PIL import Image
from transformers import (
    AutoImageProcessor,
    AutoModelForImageClassification
)


MODEL_NAME = "dennisjooo/Birds-Classifier-EfficientNetB2"

app = FastAPI(
    title="Bird AI Server"
)


print("Завантаження AI-моделі...")

try:
    processor = AutoImageProcessor.from_pretrained(MODEL_NAME)

    model = AutoModelForImageClassification.from_pretrained(
        MODEL_NAME
    )

    model.eval()

    print("AI-модель завантажено.")

except Exception as error:
    print("Помилка завантаження моделі:")
    print(error)
    raise


@app.get("/")
def home():
    return {
        "message": "Bird AI Server працює",
        "model": MODEL_NAME
    }


@app.post("/predict")
async def predict(file: UploadFile = File(...)):

    extension = file.filename.lower()

    if not (
        extension.endswith(".jpg")
        or extension.endswith(".jpeg")
        or extension.endswith(".png")
    ):
        raise HTTPException(
            status_code=400,
            detail="Підтримуються тільки JPG, JPEG та PNG"
        )

    try:
        image_bytes = await file.read()

        image = Image.open(
            io.BytesIO(image_bytes)
        ).convert("RGB")

    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Не вдалося відкрити зображення"
        )

    try:
        inputs = processor(
            images=image,
            return_tensors="pt"
        )

        with torch.no_grad():
            outputs = model(**inputs)

        probabilities = torch.softmax(
            outputs.logits,
            dim=-1
        )[0]

        top_values, top_indexes = torch.topk(
            probabilities,
            3
        )

        results = []

        for score, index in zip(
            top_values,
            top_indexes
        ):
            species = model.config.id2label[
                index.item()
            ]

            results.append({
                "species": species,
                "confidence": round(
                    score.item(),
                    4
                )
            })

        return {
            "image_name": file.filename,
            "results": results
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )

#uvicorn ai_server:app --port 8001