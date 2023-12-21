import pandas as pd
import threading
import time
import traitlets
import ipywidgets as ipw
import aiidalab_widgets_base as awb
from aiida import orm
from widget_periodictable import PTableWidget
from widget_bandsplot import BandsPlotWidget
from electronic_structure import export_bands_data, export_pdos_data

import sys
sys.path.append('/home/hungdt/works/IMMAD/codes/IMMAD')
from immad.apps.substitution import run_immad, Validator


class SetupStructureStep(ipw.VBox, awb.WizardAppWidgetStep):
    disabled = traitlets.Bool()
    configuration = traitlets.Dict()

    def __init__(self, **kwargs):
        # setup the widget for choosing the crystal structure
        # and atoms for substitution
        self.structure = awb.StructureManagerWidget(
            importers=[
                awb.StructureUploadWidget(title="From computer"),
                ],
            storable=False,
            node_class='StructureData'
            )
        
        # observe if user chooses atoms and update state
        self.structure.viewer.observe(self._update_state, ["selection"])
        
        # click on the "Confirm Structure" button locks the
        # current configuration and advance to the next step
        self.confirm_button = ipw.Button(description="Confirm Structure",
                                         disabled=True)
        self.confirm_button.on_click(self._confirm_structure)

        # We need to update the step's state
        # whenever the configuration is changed.
        self.observe(self._update_state, ["configuration"])

        super().__init__([self.structure, self.confirm_button], **kwargs)
        
    def _confirm_structure(self, button):
        "Confirm the pizza configuration and expose as trait."
        self.configuration = dict({
            'structure' : self.structure.structure,
            'substitutional' : self.structure.viewer.selection
            })
        
    def reset(self):
        with self.hold_trait_notifications():
            self.configuration = {}
            self.structure.viewer.selection = []
            
    @traitlets.default("state")
    def _default_state(self):
        return self.State.READY

    def _update_state(self, _=None):
        """Update the step's state based on traits and widget state.

        The step state influences the representation of the step 
        (e.g. the "icon") and whether the "Next step" button is enabled.
        """
        is_selected = len(self.structure.viewer.selection) != 0
        
        if self.configuration:
            self.state = self.State.SUCCESS
        elif is_selected:
            self.state = self.State.CONFIGURED
        else:
            self.state = self.State.READY

    @traitlets.observe("state")
    def _observe_state(self, change):
        # Enable the confirm button in case that some atoms
        # has been chosen for substitution
        with self.hold_trait_notifications():
            self.disabled = change["new"] == self.State.SUCCESS
            self.confirm_button.disabled = change["new"] is not self.State.CONFIGURED
        
    @traitlets.observe("disabled")
    def _observe_disabled(self, change):
        with self.hold_trait_notifications():
            for child in self.children:
                child.disabled = change["new"]
 
class ChooseSubstitutionStep(ipw.VBox, awb.WizardAppWidgetStep):
    disabled = traitlets.Bool()
    elements = traitlets.List()
    
    def __init__(self, **kwargs):
        self.periodic_widget = PTableWidget(states=1, 
                                            selected_colors=['green'], 
                                            disabled_elements=[],
                                            unselected_color='pink', 
                                            border_color='black', 
                                            width='20px')
        self.periodic_widget.observe(self._update_state, 'selected_elements')
        
        self.confirm_button = ipw.Button(description="Confirm Substitution",
                                         disabled=False)
        self.confirm_button.on_click(self._confirm_substitution)
        
        self.observe(self._update_state, ["elements"])
        
        super().__init__([self.periodic_widget, self.confirm_button],
                         **kwargs)
        
    def reset(self):
        with self.hold_trait_notifications():
            self.elements = []
            self.periodic_widget.selected_elements = {}

    def _update_state(self, _=None):
        """Update the step's state based on the order status and
        configuration traits."""
        is_selected = len(self.periodic_widget.selected_elements) > 0
        if len(self.elements) > 0:
            self.state = self.State.SUCCESS
        elif is_selected:
            self.state = self.State.CONFIGURED
        else:
            self.state = self.State.READY
            
    def _confirm_substitution(self, button):
        "Confirm the pizza configuration and expose as trait."
        self.elements = self.periodic_widget.get_elements_by_state(0)
    
    @traitlets.default("state")
    def _default_state(self):
        return self.State.READY
        
    @traitlets.observe("state")
    def _observe_state(self, change):
        """Enable the order button once the step is
        in the "configured" state."""
        with self.hold_trait_notifications():
            self.disabled = change["new"] == self.State.SUCCESS
            self.confirm_button.disabled = change["new"] is not self.State.CONFIGURED
            
    @traitlets.observe("disabled")
    def _observe_disabled(self, change):
        with self.hold_trait_notifications():
            for child in self.children:
                child.disabled = change["new"]

                
class ReviewAndPredictStep(ipw.VBox, awb.WizardAppWidgetStep):
    # We use traitlets to connect the different steps.
    # Note that we can use dlinked transformations,
    # they do not need to be of the same type.
    configuration = traitlets.Dict()
    elements = traitlets.List()
    _predicted_results = traitlets.List()

    def __init__(self, **kwargs):
        self.substituted_label = ipw.HTML('<h4>Substituted atoms</h4>')
        self.substituted_text = ipw.Output()
        
        self.substitution_label = ipw.HTML('<h4>Elements for substitutions</h4>')
        
        self.result_label = ipw.HTML('<h4>Results from the prediction</h4>')
        self.result_text = ipw.Output()
        self._predicted_results = []

        # The second step has only function: executing the order
        # by clicking on this button.
        self.predict_button = ipw.Button(description="Predict", disabled=True)
        self.predict_button.on_click(self.predict)

        # We update the step's state whenever
        # there is a change to the configuration or the order status.
        self.observe(self._update_state, ["configuration", "elements"])

        super().__init__([self.substituted_label, self.substituted_text,
                          self.substitution_label, self.result_label, 
                          self.result_text, self.predict_button], **kwargs)
        
    def reset(self):
        with self.hold_trait_notifications():
            self.configuration = {}
            self.elements = []
            self.substitution_label.value = '<h4>Elements for substitutions</h4>'
            self.result_text.clear_output()

    @traitlets.observe("configuration")
    def _observe_configuration(self, change):
        tmp = {
            'ID' : [],
            'Atom Name' : [],
            'Pos x' : [],
            'Pos y' : [],
            'Pos z' : [],
            'Mass' : [],
            'Atomic Charge' : []
        }
        if change["new"]:
            struct = change['new']['structure']
            subs = change['new']['substitutional']
            for ind in subs:
                atom = struct[ind]
                tmp['ID'].append(ind)
                tmp['Atom Name'].append(atom.symbol)
                tmp['Pos x'].append(atom.position[0])
                tmp['Pos y'].append(atom.position[1])
                tmp['Pos z'].append(atom.position[2])
                tmp['Mass'].append(atom.mass)
                tmp['Atomic Charge'].append(atom.charge)
        df = pd.DataFrame(tmp)
        df.set_index('ID', inplace=True)

        with self.substituted_text:
            self.substituted_text.clear_output()
            display(df)
        
    @traitlets.observe('elements')
    def _observe_elements(self, change):
        if change['new']:
            self.substitution_label.value += f'<pre> {", ".join(change["new"])} </pre>'

    def predict(self, button):
        "Submit the order and simulate the delivery."
        self.predict_button.disabled = True        
        self._predicted_results = run_immad(self.configuration['structure'],
                                            self.elements,
                                            self.configuration['substitutional'])
        struct = self.configuration['structure']
        with self.result_text:
            self.result_text.clear_output()
            if len(self._predicted_results) == 0:
                print('No optimal substitution found!')
            for i, sub in enumerate(self._predicted_results):
                n = sub["subs"][0]
                print(f'{i}: substitute {struct[n].symbol} ({n}) by '
                      f'{sub["subs"][1]}, score {sub["proba"]:.2f}')
        self.state = self.State.SUCCESS

    @traitlets.default("state")
    def _default_state(self):
        return self.State.READY
    
    def _update_state(self, _=None):
        """Update the step's state based on the order status and
        configuration traits."""
        if len(self.configuration) > 0 and len(self.elements) > 0:
            self.state = self.State.CONFIGURED
        else:
            self.state = self.State.INIT

    @traitlets.observe("state")
    def _observe_state(self, change):
        """Enable the order button once the step is
        in the "configured" state."""
        self.predict_button.disabled = change["new"] is not self.State.CONFIGURED

class ValidationStep(ipw.VBox, awb.WizardAppWidgetStep):
    validation_uuids = traitlets.Dict().tag(sync=True)
    _predicted_results = traitlets.List()
    
    def __init__(self, **kwargs):      
        self.relax_box = ipw.Checkbox(value=False,
                                      description='Structure Relaxation',
                                      disable=False, indent=False)
        self.band_box = ipw.Checkbox(value=False,
                                     description='Band Calculation',
                                     disable=False, indent=False)
        self.dos_box = ipw.Checkbox(value=False,
                                    description='DOS Calculation',
                                    disable=False, indent=False)
        self.phonon_box = ipw.Checkbox(value=False,
                                       description='Phonon Calculation',
                                       disable=False, indent=False)
        checkboxes = [self.relax_box, self.band_box,
                      self.dos_box, self.phonon_box]
        
        # start validation by clicking on this button.
        self.validation_button = ipw.Button(description="Validate",
                                            disabled=False)
        self.validation_button.on_click(self.validate)
        
        self.validator = Validator()

        super().__init__([ipw.HTML('<h4>What would you like to do for validation?</h4>'),
                          ipw.HBox(checkboxes),
                          ipw.HTML('<b>Note</b>: the SCF calculation is run anyway.'),
                          self.validation_button], **kwargs)
        self.update_interval = 3
        self.state = self.State.INIT
       
    def reset(self):
        with self.hold_trait_notifications():
            self.results = []
    
    def validate(self, button):
        validator = Validator()
        validator.set_relax(self.relax_box.value)
        validator.set_bands(self.band_box.value)
        validator.set_dos(self.dos_box.value)
        validator.set_phonon(self.phonon_box.value)
        self.state = self.State.CONFIGURED
        nodes = []
        for sample in self._predicted_results:
            node = validator.run(sample)
            nodes.append(node)

            # workaround to make mutable objects (such as dict)
            # to be observed by traitlets
            tmp = self.validation_uuids.copy()
            tmp[node.uuid] = False
            self.validation_uuids = tmp
        thread = threading.Thread(target=self._check_workchain_status,
                                  args=[self.update_interval])
        thread.start()

    @traitlets.observe("state")
    def _observe_state(self, change):
        """Enable the validation button once the step is
        in the "success" state."""
        self.validation_button.disabled = change["new"] is self.State.CONFIGURED

    def _check_workchain_status(self, update_interval):
        while True:
            time.sleep(update_interval)
            success = True
            uuids = self.validation_uuids.copy()
            for uuid in uuids:
                node = orm.load_node(uuid)
                if node.is_finished:
                    uuids[uuid] = True
                else:
                    success = False
            self.validation_uuids = uuids
            if success:
                self.state = self.State.SUCCESS
                break


class ResultStep(ipw.VBox, awb.WizardAppWidgetStep):
    result_uuids = traitlets.Dict().tag(sync=True)
    
    def __init__(self, **kwargs):
        self.tabs = ipw.Tab()
        super().__init__([self.tabs], **kwargs)
        self.state = self.State.INIT
        
    @traitlets.observe("result_uuids")
    def _observe_resuld_uuids(self, change):
        new = change['new']
        success = True
        for uuid, value in new.items():
            if not value:
                success = False
                continue

        # generate widgets
        n = 0
        children = []
        for uuid, value in new.items():
            if not value:
                continue
            node = orm.load_node(uuid)
            children.append(self.create_child(node))
            self.tabs.set_title(n, self.get_title(node))
            n += 1
        self.tabs.children = tuple(children)

        if success and len(new) > 0:
            self.state = self.State.SUCCESS
        
    def create_child(self, node):
        scf_parms = node.outputs.scf_parameters
        total_energy = ipw.HTMLMath(
            value=f"$E = {scf_parms['energy']} eV$",
            placeholder='Total energy',
            description='Total energy: ')
        fermi_level = ipw.HTMLMath(
            value=f"$\epsilon_F = {scf_parms['fermi_energy']} eV$",
            placeholder='Fermi level',
            description='Fermi level: ')
        structure = awb.viewer(node.outputs.structure)
        band_dos_label = ipw.Label(value='Band structure and DOS')
        band_dos = self.get_bands_dos_widget(node)
        return ipw.VBox([total_energy, fermi_level, structure,
                         band_dos_label, band_dos])
    
    def get_title(self, node):
        return node.outputs.structure.get_formula()
    
    def get_bands_dos_widget(self, node):
        fermi_level = node.outputs.scf_parameters['fermi_energy']
        bands_data = export_bands_data(node.outputs, fermi_level)
        dos_data = export_pdos_data(node.outputs, fermi_level)
        return BandsPlotWidget(bands=bands_data, dos=dos_data,
                               plot_fermilevel=True, show_legend=True,
                               energy_range = {"ymin": -10.0, "ymax": 10.0})
