
import logging

from .. import orngSignalManager
from .scheme import Scheme
from .utils import name_lookup
from ..config import rc

log = logging.getLogger(__name__)


class WidgetsScheme(Scheme):
    """A Scheme containing Orange Widgets managed with a SignalManager
    instance.

    """
    def __init__(self, parent=None, title=None, description=None):
        Scheme.__init__(self, parent, title, description)

        self.widgets = []
        self.widget_for_node = {}
        self.signal_manager = orngSignalManager.SignalManager()

        self.__loaded_from = None

    def add_node(self, node):
        widget = self.create_widget_instance(node)
        Scheme.add_node(self, node)
        self.widgets.append(widget)

        self.widget_for_node[node] = widget

        self.signal_manager.addWidget(widget)

    def remove_node(self, node):
        Scheme.remove_node(self, node)
        widget = self.widget_for_node[node]
        self.signal_manager.removeWidget(widget)
        del self.widget_for_node[node]

        # Save settings to user global settings.
        if not self.__loaded_from:
            widget.saveSettings()

        # Notify the widget it will be deleted.
        widget.onDeleteWidget()
        # And schedule it for deletion.
        widget.deleteLater()

    def add_link(self, link):
        Scheme.add_link(self, link)
        source_widget = self.widget_for_node[link.source_node]
        sink_widget = self.widget_for_node[link.sink_node]
        source_channel = link.source_channel.name
        sink_channel = link.sink_channel.name
        self.signal_manager.addLink(source_widget, sink_widget, source_channel,
                                    sink_channel, enabled=link.enabled)
        from functools import partial
        self.signal_manager.processNewSignals()
        link.enabled_changed.connect(
            partial(self.signal_manager.setLinkEnabled,
                    source_widget, sink_widget)
        )

    def remove_link(self, link):
        Scheme.remove_link(self, link)

        source_widget = self.widget_for_node[link.source_node]
        sink_widget = self.widget_for_node[link.sink_node]
        source_channel = link.source_channel.name
        sink_channel = link.sink_channel.name

        self.signal_manager.removeLink(source_widget, sink_widget,
                                       source_channel, sink_channel)

    def create_widget_instance(self, node):
        desc = node.description
        klass = name_lookup(desc.qualified_name)

        log.info("Creating %r instance.", klass)
        widget = klass.__new__(
            klass,
            _owInfo=rc.get("canvas.show-state-info", True),
            _owWarning=rc.get("canvas.show-state-warning", True),
            _owError=rc.get("canvas.show-state-error", True),
            _owShowStatus=rc.get("OWWidget.show-status", True),
            _useContexts=rc.get("OWWidget.use-contexts", True),
            _category=desc.category,
            _settingsFromSchema=node.properties
        )
        import pprint
        log.debug("New %r instance properties:\n%s", node.title,
                  pprint.pformat(node.properties))

        widget.__init__(None, self.signal_manager)
        widget.setCaption(node.title)
        widget.widgetInfo = desc

        widget.setVisible(node.properties.get("visible", False))

        node.title_changed.connect(widget.setCaption)
        # Bind widgets progress/processing state back to the node's properties
        widget.progressBarValueChanged.connect(node.set_progress)
        widget.processingStateChanged.connect(node.set_processing_state)

        return widget

    def close_all_open_widgets(self):
        for widget in self.widget_for_node.values():
            widget.close()

    def sync_node_properties(self):
        """Sync the widget settings/properties with the SchemeNode.properties.
        Return True if there were any changes in the properties (i.e. if the
        new node.properties differ from the old value) and False otherwise.

        .. note:: this should hopefully be removed in the feature, when the
            widget can notify a changed setting property.

        """
        changed = False
        for node in self.nodes:
            widget = self.widget_for_node[node]
            settings = widget.getSettings()
            if settings != node.properties:
                node.properties = settings
                changed = True
        log.debug("Scheme node properties sync (changed: %s)", changed)
        return changed

    def save_to(self, stream):
        self.sync_node_properties()
        Scheme.save_to(self, stream)

    def load_from(self, stream):
        """Load the scheme from xml formated stream.
        """
        if isinstance(stream, basestring):
            self.__loaded_from = stream
            stream = open(stream, "rb")
        elif isinstance(stream, file):
            self.__loaded_from = stream.name

        Scheme.load_from(self, stream)
