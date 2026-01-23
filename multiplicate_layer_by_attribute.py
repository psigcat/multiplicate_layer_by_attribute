from qgis.core import Qgis, QgsProject, QgsMapLayerType, QgsLayerTreeLayer, QgsFeatureRequest

from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction

from .multiplicate_layer_by_attribute_dialog import multiplicate_layer_by_attributeDialog
import os.path


class multiplicate_layer_by_attribute:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor."""
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
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
        self.active_layer = None
        self.active_field = None


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
            text=self.tr(u'Parcs i Jardins Manager'),
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
            self.on_active_layer_changed()
            self.iface.layerTreeView().currentLayerChanged.connect(self.on_active_layer_changed)
            self.dlg.layer_list.layerChanged.connect(lambda:self.on_active_layer_changed(True))
            self.dlg.field_list.fieldChanged.connect(self.on_active_field_changed)

        self.dlg.show()
        result = self.dlg.exec_()

        if result:
            print("execute")

            if not self.active_layer or self.active_layer.type() != QgsMapLayerType.VectorLayer:
                self.dlg.messageBar.pushMessage("Select a layer in order to execute process", level=Qgis.Warning)
                return

            if not self.active_field:
                self.dlg.messageBar.pushMessage("Select a field in order to execute process", level=Qgis.Warning)
                return

            self.create_multiple_layers(self.active_layer, self.active_field)


    def on_active_layer_changed(self, ui_change=False):
        """ active layer changed """

        # if ui_change:
        #     # layer changed in plugin UI
        #     self.active_layer = self.dlg.layer_list.currentLayer()

        #     if self.active_layer and self.active_layer.type() == QgsMapLayerType.VectorLayer:
        #         print(f"1 Active layer changed to: {self.active_layer.name()}")
        #         self.iface.setActiveLayer(self.active_layer)
        #         self.dlg.field_list.setLayer(self.active_layer)
        
        # else:
            # layer changed in QGIS layer tree
        self.active_layer = self.iface.activeLayer()

        if self.active_layer and self.active_layer.type() == QgsMapLayerType.VectorLayer:
            print(f"2 Active layer changed to: {self.active_layer.name()}")
            # active_layer = QgsProject.instance().layer(QgsProject.instance().layerTreeRoot().currentLayer().id())
            self.dlg.layer_list.setLayer(self.active_layer)
            self.dlg.field_list.setLayer(self.active_layer)

        if not self.active_layer or self.active_layer.type() != QgsMapLayerType.VectorLayer:
            self.iface.setActiveLayer(None)
            self.dlg.layer_list.setLayer(None)
            self.dlg.field_list.setLayer(None)
        
        print(self.active_layer)


    def on_active_field_changed(self, none_selected=False):
        """ active field changed """

        self.active_field = self.dlg.field_list.currentField()
        print(f"Active field changed to: {self.active_field}")

        if self.active_field == "":
            return

        # get all unique values
        unique_values = self.active_layer.uniqueValues(self.active_layer.fields().indexFromName(self.active_field))

        for field_value in sorted(unique_values):
            # TODO: cast to string
            self.dlg.field_values.addItem(field_value)

        self.dlg.resume_msg.setText(f"{len(unique_values)} layers will be created.")


    def create_multiple_layers(self, layer, field):
        """ clone layer with all unique selected field values """

        # create group
        parent = QgsProject.instance().layerTreeRoot()
        layer_group = parent.addGroup(field)

        # get all unique values
        unique_values = self.active_layer.uniqueValues(self.active_layer.fields().indexFromName(self.active_field))

        for field_value in sorted(unique_values):
            # Get the value from the active field fetching first feature that matches this class
            filter_expression = f'"{field}" = \'{field_value}\''
            req = QgsFeatureRequest().setFilterExpression(filter_expression)
            feature = next(layer.getFeatures(req), None)

            if feature:
                #brigada_val = feature[target_field]

                if field_value and field_value != "":
                    print(field_value)

                    # duplicate layer and apply Provider Feature Filter
                    new_layer = layer.clone()
                    new_layer.setName(str(field_value))
                    new_layer.setSubsetString(filter_expression)

                    QgsProject.instance().addMapLayer(new_layer, False)
                    layer_group.addChildNode(QgsLayerTreeLayer(new_layer))

