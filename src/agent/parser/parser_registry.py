from agent.parser.base_parser import BaseParser
from agent.state.entity.state_entity import BaseStateEntity


class ParserRegistry:
    def __init__(self):
        self._parsers: dict[type[BaseStateEntity], BaseParser] = {}

    def register(self, entity_class: type[BaseStateEntity], parser: BaseParser) -> None:
        self._parsers[entity_class] = parser

    def get_parser(self, entity_class: type[BaseStateEntity]) -> BaseParser | None:
        if entity_class in self._parsers:
            return self._parsers[entity_class]

        for registered_class, parser in self._parsers.items():
            if issubclass(entity_class, registered_class):
                return parser

        return None


_default_registry: ParserRegistry | None = None


def get_default_registry() -> ParserRegistry:
    global _default_registry
    if _default_registry is None:
        _default_registry = ParserRegistry()
    return _default_registry


def register_parser(entity_class: type[BaseStateEntity], parser: BaseParser) -> None:
    get_default_registry().register(entity_class, parser)


def get_parser_for_entity(entity_class: type[BaseStateEntity]) -> BaseParser | None:
    return get_default_registry().get_parser(entity_class)
