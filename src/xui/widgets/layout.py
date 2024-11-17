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
        for child, child_height in zip(self.children, heights):
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
        for child, child_width in zip(self.children, widths):
            child.set_width(child_width)
            child.x = x
            x += child_width + self.spacing
            child.hlayout()


class HSpacer(Widget):
    greedy_width = True


class VSpacer(Widget):
    greedy_height = True
