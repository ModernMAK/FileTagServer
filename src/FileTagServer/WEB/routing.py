files_route = f"/files"
file_route = f"{files_route}/{{file_id}}"
file_edit_route = f"{files_route}/{{file_id}}/edit"
file_edit_submit_route = file_edit_route
file_data_route = f"{files_route}/{{file_id}}/data"
file_preview_route = f"{files_route}/{{file_id}}/preview"

tags_route = f"/tags"
tag_route = f"{tags_route}/{{tag_id}}"

folders_route = f"/folders"
folder_route = f"{folders_route}/{{folder_id}}"

root_route = "/"
orphaned_files_route = "/orphaned_files"
