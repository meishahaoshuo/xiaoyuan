from flask import request, current_app


def get_page():
    """Get the current page number from request args."""
    try:
        page = int(request.args.get('page', 1))
        return max(1, page)
    except (ValueError, TypeError):
        return 1


def paginate(query, per_page=None):
    """Paginate a SQLAlchemy query. Returns a Pagination object."""
    if per_page is None:
        per_page = current_app.config.get('ITEMS_PER_PAGE', 12)
    page = get_page()
    return query.paginate(page=page, per_page=per_page, error_out=False)
