from qgis.core import Qgis, QgsProject, QgsMapLayerType, QgsLayerTreeLayer, QgsFeatureRequest, QgsExpression, QgsExpressionContext, QgsExpressionContextUtils
from qgis.gui import QgsExpressionBuilderDialog

from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction

from .multiplicate_layer_by_attribute_dialog import multiplicate_layer_by_attributeDialog

import os.path


class multiplicate_layer_by_attribute:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor."""

        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)

        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'multiplicate_layer_by_attribute_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&Multiplicate layer by attribute')

        self.first_start = None


    def tr(self, message):
        """Get the translation for a string using Qt translation API."""

        return QCoreApplication.translate('multiplicate_layer_by_attribute', message)


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar."""

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.iface.addToolBarIcon(action)

        if add_to_menu:
            self.iface.addPluginToMenu(self.menu, action)

        self.actions.append(action)

        return action


    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = self.plugin_dir + '/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Multiplicate layer by attribute'),
            callback=self.run,
            parent=self.iface.mainWindow())

        self.first_start = True


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""

        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&Multiplicate layer by attribute'),
                action)
            self.iface.removeToolBarIcon(action)


    def run(self):
        """Run method that performs all the real work"""

        if self.first_start == True:
            self.first_start = False
            self.dlg = multiplicate_layer_by_attributeDialog()

            self.dlg.layer_list.setAllowEmptyLayer(True, "Select")
            self.dlg.field_list.setAllowEmptyFieldName(True)

            if self.iface.activeLayer():
                self.sync_tree_to_plugin(self.iface.activeLayer())

            self.iface.layerTreeView().currentLayerChanged.connect(self.sync_tree_to_plugin)
            self.dlg.layer_list.layerChanged.connect(self.sync_plugin_to_tree)
            self.dlg.field_list.fieldChanged.connect(self.on_active_field_changed)

        self.dlg.show()
        result = self.dlg.exec_()

        if result:
            print("execute")

            if not self.dlg.layer_list.currentLayer():
                self.dlg.messageBar.pushMessage("Select a layer in order to execute process", level=Qgis.Warning)
                return

            #if self.dlg.field_list.currentField() == "":
            if self.dlg.field_list.expression() == "":
                self.dlg.messageBar.pushMessage("Select a field in order to execute process", level=Qgis.Warning)
                return

            self.create_multiple_layers()


    def sync_tree_to_plugin(self, layer):
        """Updates the combo box when the QGIS active layer changes."""

        if layer and layer.type() == QgsMapLayerType.VectorLayer:
            # Block signals to prevent triggering sync_plugin_to_tree back
            self.dlg.layer_list.blockSignals(True)
            self.dlg.layer_list.setLayer(layer)
            self.dlg.field_list.setLayer(layer)
            self.dlg.layer_list.blockSignals(False)


    def sync_plugin_to_tree(self, layer):
        """Updates the QGIS active layer when the combo box changes."""

        if layer:
            # Set the layer as active in the QGIS interface
            self.iface.setActiveLayer(layer)
            self.dlg.field_list.setLayer(layer)
            self.dlg.field_list.setField("")


    def on_active_field_changed(self, none_selected=False):
        """ active field changed """

        self.dlg.field_values.clear()

        unique_values = self.get_unique_values()
        
        if not unique_values:
            return

        # Convert all values to strings first to ensure they can be sorted and added
        string_values = [str(val) if val is not None else "NULL" for val in unique_values]

        for field_value in sorted(string_values):
            self.dlg.field_values.addItem(field_value)

        self.dlg.resume_msg.setText(f"{len(unique_values)} layers will be created.")


    def get_unique_values(self):
        """ get unique field values from field name or expression """

        active_layer = self.iface.activeLayer()
        active_field = self.dlg.field_list.expression()

        if not active_field or active_field == "":
            return

        field_index = active_layer.fields().lookupField(active_field)

        if field_index != -1:
            unique_values = active_layer.uniqueValues(field_index)
        else:
            expr = QgsExpression(active_field)
            context = QgsExpressionContext()
            context.appendScopes(QgsExpressionContextUtils.globalProjectLayerScopes(active_layer))
            
            expr.prepare(context)
            
            unique_values = set()
            for feature in active_layer.getFeatures():
                context.setFeature(feature)
                value = expr.evaluate(context)
                unique_values.add(value)

        return unique_values


    def hide_all_layers_but(self, group, target_layer_name=False):
        """ Hide all layers inside a layer group but given """

        for child in group.children():
            if isinstance(child, QgsLayerTreeLayer):
                visible = target_layer_name and child.name() == target_layer_name
                child.setItemVisibilityChecked(visible)


    def create_multiple_layers(self):
        """ clone layer with all unique selected field values """

        unique_values = self.get_unique_values()

        if not unique_values:
            return

        active_layer = self.iface.activeLayer()
        active_field = self.dlg.field_list.expression()

        if not active_field or active_field == "":
            return

        # add "" to field names, but not expressions
        field_index = active_layer.fields().lookupField(active_field)
        if field_index != -1:
            active_field = '"' + active_field + '"'

        # create group
        parent = QgsProject.instance().layerTreeRoot()
        layer_group = parent.addGroup(active_field)

        # stop the canvas from updating
        canvas = self.iface.mapCanvas()
        canvas.freeze(True)

        new_layers = []
        first_layer = None

        for field_value in sorted(unique_values):

            if field_value and field_value != "":

                # Get the value from the active field fetching first feature that matches this class
                filter_expression = f'{active_field} = \'{field_value}\''
                print(filter_expression)

                req = QgsFeatureRequest().setFilterExpression(filter_expression)
                feature = next(active_layer.getFeatures(req), None)

                if feature:

                    # duplicate layer and apply Provider Feature Filter
                    new_layer = active_layer.clone()
                    new_layer.setName(str(field_value))
                    new_layer.setSubsetString(filter_expression)
                    new_layers.append(new_layer)
                    layer_group.addChildNode(QgsLayerTreeLayer(new_layer))

                    # zoom to first layer
                    if not first_layer:
                        first_layer = new_layer

        QgsProject.instance().addMapLayers(new_layers, False)
        self.hide_all_layers_but(layer_group, first_layer.name())

        self.iface.setActiveLayer(first_layer)
        self.iface.mapCanvas().zoomToSelected(first_layer)

        # enable and refresh the canvas
        canvas.freeze(False)
        canvas.refresh()

        print("done")
