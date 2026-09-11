import cubit
import json
print("FCMODEL_IMPORT_DONE=" + json.dumps({"errors": cubit.get_error_count(), "nodes": cubit.get_node_count(), "elements": cubit.get_element_count(), "version": cubit.get_version()}))
result = cubit.cmd('export fidesyscase "/home/antonov/Base/Libs/FCModel/work/1_2_2026-09-11_fidesys_roundtrip_pilot/Cube_static_direction_shell.fc" overwrite')
print("FCMODEL_EXPORT_DONE=" + json.dumps({"errors": cubit.get_error_count(), "nodes": cubit.get_node_count(), "elements": cubit.get_element_count(), "result": result}))
