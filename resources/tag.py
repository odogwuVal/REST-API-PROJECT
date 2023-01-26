from flask.views import MethodView
from flask_smorest import abort, Blueprint
from schemas import TagSchema, TagAndItemSchema

from db import db
from models import StoreModel, TagModel, ItemModel
from sqlalchemy.exc import SQLAlchemyError

blp = Blueprint("Tags", "tags", description="operations on tags")

@blp.route("/store/<string:store_id>/tag")
class TagsInStore(MethodView):
    @blp.response(200, TagSchema(many=True))
    def get(self, store_id):
        store = StoreModel.query.get_or_404(store_id)
        return store.tags.all()

    @blp.arguments(TagSchema)
    @blp.response(201, TagSchema)
    def post(self, tag_data, store_id):
        tag = TagModel(**tag_data, store_id=store_id)

        try:
            db.session.add(tag)
            db.session.commit()
        except SQLAlchemyError as e:
            abort(
                500,
                message=str(e)
            )

        return tag

@blp.route("/tag/<string:tag_id>")
class Tag(MethodView):
    @blp.response(201, TagSchema)
    def get(self, tag_id):
        tag = TagModel.query.get_or_404(tag_id)
        return tag

    @blp.response(202, 
    description="Deletes a tag if not item is tagged with it",
    example={"message": "Tag deleted"}
    )
    @blp.alt_response(404, 
    description="Tag not found"
    )
    @blp.alt_response(404, 
    description="Returned if the tag is assigned to one or more items. In this case, the tag is not deleted"
    )
    def delete(self, tag_id):
        tag = TagModel.query.get_or_404(tag_id)
        if not tag.items:
            db.session.delete(tag)
            db.session.commit()
            return {"message": "Tag deleted"}
        abort(500, message="Could not delete tag. Make sure Tag is not associated with any items then try again")

@blp.route("/item/<string:item_id>/tag/<string:tag_id>")
class LinkTagsToItem(MethodView):
    @blp.response(201, TagSchema)
    def post(self, item_id, tag_id):
        item = ItemModel.query.get_or_404(item_id)
        tag = TagModel.query.get_or_404(tag_id)

        item.tags.append(tag)

        try:
            db.session.add(item)
            db.session.commit()
        except SQLAlchemyError as e:
            abort(500, message="Error occured while inserting the Tag")
        
        return tag

    @blp.response(201, TagAndItemSchema)
    def delete(self, item_id, tag_id):
        item = ItemModel.query.get_or_404(item_id)
        tag = TagModel.query.get_or_404(tag_id)

        item.tags.remove(tag)

        try:
            db.session.add(item)
            db.session.commit()
        except SQLAlchemyError as e:
            abort(500, message="Error occured while removing the Tag")
        
        return {"message": "Item removed from Tag", "Item": item, "tag": tag}