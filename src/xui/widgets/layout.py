from ..widget import Widget


def divide_space(total_space, min_sizes, max_sizes):
    if sum(max_sizes) <= total_space:
        return max_sizes

    remaining_space = total_space - sum(min_sizes)
    assert remaining_space >= 0
    if remaining_space == 0:
        return min_sizes

    sizes = list(min_sizes)
    elements = [(hi - lo, i) for i, (lo, hi) in enumerate(zip(min_sizes, max_sizes))]
    elements.sort() # sort by the amount element can grow by
    per_element, rem = divmod(remaining_space, len(elements))
    for gi, (headroom, i) in enumerate(elements):
        target_grow_by = per_element + (1 if (len(elements) - gi <= rem) else 0)
        grow_by = min(target_grow_by, headroom)
        sizes[i] += grow_by
        assert min_sizes[i] <= sizes[i] <= max_sizes[i]
        remaining_space -= grow_by
        if grow_by < target_grow_by:
            per_element, rem = divmod(remaining_space, len(elements) - gi - 1)

    assert sum(sizes) == total_space
    return sizes


def _max(x):
    l = list(x)
    return max(l) if l else 0


class VBox(Widget):
    def min_contents_height(self):
        total_spacing = self.spacing * (len(self.children) - 1)
        return total_spacing + sum(child.min_height() for child in self.children)

    def max_contents_height(self):
        total_spacing = self.spacing * (len(self.children) - 1)
        return total_spacing + sum(child.max_height() for child in self.children)

    def vlayout(self):
        y = self.y + self.margin
        height = self.height - 2 * self.margin - self.spacing * (len(self.children) - 1)
        min_heights = [child.min_height() for child in self.children]
        if sum(min_heights) > height:
            self.error("height=%d, avail=%d, children require %r", self.height, height, min_heights)
        max_heights = [child.max_height() for child in self.children]
        heights = divide_space(height, min_heights, max_heights)
        leftover = height - sum(heights)
        for child, child_height in zip(self.children, heights):
            if leftover and (child.valign or self.child_valign) == 'fill':
                child_height += leftover
                leftover = 0
            child.set_height(child_height)
            child.y = y
            y += child_height + self.spacing
            child.vlayout()


class HBox(Widget):
    def min_contents_width(self):
        total_spacing = self.spacing * (len(self.children) - 1)
        return total_spacing + sum(child.min_width() for child in self.children)

    def max_contents_width(self):
        total_spacing = self.spacing * (len(self.children) - 1)
        return total_spacing + sum(child.max_width() for child in self.children)

    def hlayout(self):
        x = self.x + self.margin
        width = self.width - 2 * self.margin - self.spacing * (len(self.children) - 1)
        min_widths = [child.min_width() for child in self.children]
        if sum(min_widths) > width:
            self.error("width=%d, avail=%d, children require %r", self.width, width, min_widths)
        max_widths = [child.max_width() for child in self.children]
        widths = divide_space(width, min_widths, max_widths)
        leftover = width - sum(widths)
        for child, child_width in zip(self.children, widths):
            if leftover and (child.halign or self.child_halign) == 'fill':
                child_width += leftover
                leftover = 0
            child.set_width(child_width)
            child.x = x
            x += child_width + self.spacing
            child.hlayout()


class GridBox(Widget):
    def __init__(self, rows=None, **kwargs):
        self.rows = rows or []
        children = [cell for row in self.rows for cell in row if cell]
        super().__init__(children, **kwargs)
        self.rows_updated()

    def rows_updated(self):
        self.children = [cell for row in self.rows for cell in row if cell]
        self.n_cols = len(self.rows[0]) if self.rows else 0
        self.n_rows = len(self.rows)
        self.cols = [[row[col_i] for row in self.rows] for col_i in range(self.n_cols)]

    def min_contents_width(self):
        total_spacing = self.spacing * (self.n_cols - 1)
        min_widths = [_max(cell.min_width() for cell in col if cell) for col in self.cols]
        return total_spacing + sum(min_widths)

    def max_contents_width(self):
        total_spacing = self.spacing * (self.n_cols - 1)
        max_widths = [_max(cell.max_width() for cell in col if cell) for col in self.cols]
        return total_spacing + sum(max_widths)

    def min_contents_height(self):
        total_spacing = self.spacing * (self.n_rows - 1)
        min_heights = [_max(cell.min_height() for cell in row if cell) for row in self.rows]
        return total_spacing + sum(min_heights)

    def max_contents_height(self):
        total_spacing = self.spacing * (self.n_rows - 1)
        max_heights = [_max(cell.max_height() for cell in row if cell) for row in self.rows]
        return total_spacing + sum(max_heights)

    def hlayout(self):
        x = self.x + self.margin
        width = self.width - 2 * self.margin - self.spacing * (self.n_cols - 1)
        min_widths = [_max(cell.min_width() for cell in col if cell) for col in self.cols]
        max_widths = [_max(cell.max_width() for cell in col if cell) for col in self.cols]
        if sum(min_widths) > width:
            self.error("width=%d, avail=%d, children require %r", self.width, width, min_widths)
        widths = divide_space(width, min_widths, max_widths)
        for col, col_width in zip(self.cols, widths):
            for child in col:
                if not child:
                    continue
                child.x = x
                child_width = min(col_width, child.max_width())
                if child.halign == 'fill':
                    child_width = col_width
                child.set_width(child_width)
                if child_width < col_width:
                    gap = col_width - child_width
                    align = child.halign or self.halign
                    offset = gap * (1 if align == 'right' else 0.5 if align == 'center' else 0)
                    child.x += offset
                child.hlayout()
            x += col_width + self.spacing

    def vlayout(self):
        y = self.y + self.margin
        height = self.height - 2 * self.margin - self.spacing * (self.n_rows - 1)
        min_heights = [_max(cell.min_height() for cell in row if cell) for row in self.rows]
        max_heights = [_max(cell.max_height() for cell in row if cell) for row in self.rows]
        if sum(min_heights) > height:
            self.error("height=%d, avail=%d, children require %r", self.height, height, min_heights)
        heights = divide_space(height, min_heights, max_heights)
        for row, row_height in zip(self.rows, heights):
            for child in row:
                if not child:
                    continue
                child.y = y
                child_height = min(row_height, child.max_height())
                if child.valign == 'fill':
                    child_height = row_height
                child.set_height(child_height)
                if child_height < row_height:
                    gap = row_height - child_height
                    align = child.valign or self.valign
                    offset = gap * (1 if align == 'bottom' else 0.5 if align == 'center' else 0)
                    child.y += offset
                child.vlayout()
            y += row_height + self.spacing


class HSpacer(Widget):
    greedy_width = True


class VSpacer(Widget):
    greedy_height = True
