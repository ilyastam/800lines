from agent.parser.base_parser import BaseParser
from agent.state.entity.state_entity import BaseStateEntity


class ParserRegistry:
    def __init__(self):
        self._parsers: dict[str | None, dict[type[BaseStateEntity], BaseParser]] = {}

    def register(self, parser: BaseParser) -> None:
        for channel_domain in parser.channel_domains:
            domain_parsers = self._parsers.setdefault(channel_domain, {})
            for entity_class in parser.entity_classes:
                domain_parsers[entity_class] = parser

    def get_parser(
        self, entity_class: type[BaseStateEntity], channel_domain: str | None = None
    ) -> BaseParser | None:
        for domain in (channel_domain, None):
            domain_parsers = self._parsers.get(domain, {})
            if entity_class in domain_parsers:
                return domain_parsers[entity_class]

            for registered_class, parser in domain_parsers.items():
                if issubclass(entity_class, registered_class):
                    return parser

        return None


_default_registry: ParserRegistry | None = None


def get_default_registry() -> ParserRegistry:
    global _default_registry
    if _default_registry is None:
        _default_registry = ParserRegistry()
    return _default_registry


def register_parser(parser: BaseParser) -> None:
    get_default_registry().register(parser)


def get_parser_for_entity(
    entity_class: type[BaseStateEntity], channel_domain: str | None = None
) -> BaseParser | None:
    return get_default_registry().get_parser(entity_class, channel_domain)
