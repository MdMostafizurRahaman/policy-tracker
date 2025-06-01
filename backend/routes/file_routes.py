from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from bson import ObjectId
import mimetypes
import io

from ..services.file_service import get_file_from_db
from database.connection import get_db

router = APIRouter(prefix="/api", tags=["files"])

@router.get("/file/{file_id}")
async def download_file(file_id: str, db=Depends(get_db)):
    try:
        file_doc = await get_file_from_db(db.files, file_id)
        content_type = file_doc.get("content_type") or mimetypes.guess_type(file_doc["filename"])[0] or "application/octet-stream"
        
        def iterfile():
            yield file_doc["file_data"]
        
        return StreamingResponse(
            iterfile(),
            media_type=content_type,
            headers={"Content-Disposition": f"attachment; filename={file_doc['filename']}"}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))