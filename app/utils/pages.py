# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from math import ceil, floor


def page_numbering(total_count, limit, skip, max_pages=5):
    total_page = ceil(total_count/limit)
    current_page = floor(skip/limit) + 1
    pages = [(page + 1, limit, limit * page) for page in range(total_page)]
    if current_page == total_page:
        _start = max(current_page - max_pages, 0)
        return pages[_start:], current_page
    elif current_page == 1:
        return pages[:max_pages], current_page
    else:
        return page_numbering_general_case(
            max_pages, current_page, total_page, pages
        )


def page_numbering_general_case(max_pages, current_page, total_page, pages):
    remain = 0
    delta_before = floor(max_pages/2)
    delta_after = floor(max_pages/2)
    if current_page - delta_before < 0:
        delta_after = delta_after + delta_before - current_page
        delta_before = current_page - 1
    if current_page + delta_after > total_page:
        remain = current_page + delta_after - total_page
    if current_page - delta_before - remain <= 0:
        delta_before = current_page - 1
    if max_pages > 2 * current_page - delta_before - 1 + delta_after:
        delta_after = delta_after + 1
    return pages[current_page - delta_before - 1: current_page + delta_after], current_page
