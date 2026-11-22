(* Headless helper: generate the finished map of a region and write it as a PNG.
   Usage: dump_map.exe REGION_INDEX SEED OUT.png   (REGION_INDEX 4 = Netherlands) *)
open Containers
open Rails_lib

let () =
  let region_idx = int_of_string Sys.argv.(1) in
  let seed = int_of_string Sys.argv.(2) in
  let out = Sys.argv.(3) in
  let region = Region.of_enum region_idx |> Option.get_exn_or "bad region" in
  let res = Resources.load_all () in
  let random = Random.State.make [|seed|] in
  let map = List.assoc ~eq:(Stdlib.(=)) region res.Resources.res_maps |> Tilemap.of_ndarray ~region ~seed in
  let cities = List.assoc ~eq:(Stdlib.(=)) region res.Resources.res_cities
    |> List.map (fun (name, x, y) -> (x, y, name)) in
  let map = Mapgen.generate_headless random region cities map in
  Printf.printf "%s: %d cities\n" (Region.show region) (List.length cities);
  let year = Region.start_year region in
  Train_engine.of_region region |> Train_engine.randomize_year random
  |> Train_engine.available_at_year ~year
  |> List.iter (fun (e:Train_engine.t) -> Printf.printf "  %d: %s (%d)\n" year e.name e.year);
  Engine.Pic.png_of_ndarray (Tilemap.to_ndarray map.Tilemap.map) ~filename:out
