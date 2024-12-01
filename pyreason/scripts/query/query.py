from pyreason.scripts.utils.query_parser import parse_query


class Query:
    def __init__(self, query_text: str):
        """
        PyReason query object which is parsed from a string of form:
            `pred(node)` or `pred(edge)` or `pred(node) : [l, u]`
        If bounds are not specified, they are set to [1, 1] by default. A tilde `~` before the predicate means that the bounds
        are inverted, i.e. [0, 0] for [1, 1] and vice versa.

        Queries can be used to analyze the graph and extract information about the graph after the reasoning process.
        Queries can also be used as input to the reasoner to filter the ruleset based which rules are applicable to the query.

        :param query_text: The query string of form described above
        """
        self.__pred, self.__component, self.__comp_type, self.__bnd = parse_query(query_text)
        self.query_text = query_text

    def get_predicate(self):
        return self.__pred

    def get_component(self):
        return self.__component

    def get_component_type(self):
        return self.__comp_type

    def get_bounds(self):
        return self.__bnd

    def __str__(self):
        return self.query_text

    def __repr__(self):
        return self.query_text
