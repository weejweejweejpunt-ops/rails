open Containers

module Pic = Engine.Pic
module Paths = Engine.Paths

let map_names =
  let open Region in
  [
    EastUS, "EASTUS.PIC";
    WestUS, "WESTUS.PIC";
    Britain, "BRITAIN.PIC";
    Europe, "EUROPE.PIC";
    Netherlands, "NETHERLANDS.png";
  ]

let load_pics () =
  let load_ndarray ~transparent s = Pic.img_of_file ~transparent (Paths.data_file s) in
  let transparent = [
    (* E and C versions are for England and Europe *)
    "SPRITES.PIC"; "CSPRITES.PIC"; "ESPRITES.PIC"; "SPRITES_extra.png";
    "TRACKS.PIC"; "TRACKS_extra.png"; "STATION.PIC"; "ESTATION.PIC";
    "BRITAIN.PIC";
    "LOCOS.PIC"; "CLOCOS.PIC"; "CLOCOSM.PIC"; "ELOCOS.PIC";
    "ELOCOSM.PIC"; "LOCOSM.PIC";
  ] in
  let nontransparent = [
    "ELOCOS0.PIC"; "ELOCOS1.PIC"; "ELOCOS2.PIC"; "ELOCOS3.PIC"; 
    "LOCOS0.PIC"; "LOCOS1.PIC"; "LOCOS2.PIC"; "FACES.PIC";
    "LOGO.PIC"; "LABS.PIC"; "CREDITS2.PIC"; "ADVERT.PIC";
    "PAGE0.PIC"; "PAGE1.PIC"; "PAGE2.PIC"; "PAGE3.PIC"; "PAGE4.PIC";
    "PAGE5.PIC"; "PAGE6.PIC"; "PAGE7.PIC"; "PAGE8.PIC"; "PAGE9.PIC";
    "TITLE.PIC";
    "DIFFS.PIC"; "DIFFSP.PIC"; "COUNCIL.PIC";
    "NETHERLANDS_MENU.png";
  ] in
  let images = Hashtbl.create 20 in
  List.iter (fun s ->
    let ndarray = load_ndarray ~transparent:true s in
    Hashtbl.replace images (Filename.chop_extension s) ndarray)
  transparent;
  List.iter (fun s ->
    let ndarray = load_ndarray ~transparent:false s in
    Hashtbl.replace images (Filename.chop_extension s) ndarray)
  nontransparent;
  images

module Ndarray = Owl_base_dense_ndarray.Generic
type ndarray = (int, Bigarray.int8_unsigned_elt) Ndarray.t

(* All game resources *)
type t = {
  res_maps: (Region.t * ndarray) list;
  res_pics: (string, Pic.ndarray) Hashtbl.t;
  res_cities: (Region.t * (string * int * int) list) list;
}

(* The start-menu background (DIFFS.PIC) shows a board with room for four area names.
   The Netherlands needs a fifth line, so the board's top edge is moved up: the old top border is
   copied [menu_board_extra_height] rows higher and the gap is filled with board interior.
   (Pixel coordinates were measured on the original DIFFS.PIC: the board spans x 42-137, its top
   border is rows 22-26 and its interior starts at row 27.) *)
let menu_board_extra_height = 10

let extend_menu_board (img: Pic.ndarray) =
  let x0, x1 = 42, 137 in
  let border_top, border_bottom = 22, 26 in
  let interior_row = 30 in
  let dy = menu_board_extra_height in
  for x = x0 to x1 do
    for c = 0 to 3 do
      for y = border_top to border_bottom do
        Ndarray.set img [|y - dy; x; c|] (Ndarray.get img [|y; x; c|])
      done;
      for y = border_top - dy + (border_bottom - border_top + 1) to border_bottom do
        Ndarray.set img [|y; x; c|] (Ndarray.get img [|interior_row; x; c|])
      done
    done
  done

let load_all () =
  let res_maps =
    List.map (fun (region,s) -> region, Paths.data_file s
      |> Tilemap.ndarray_of_file) map_names
  in
  let res_cities = List.map Mapgen.load_city_list Region.regions |> 
    List.combine Region.regions
  in
  let res_pics = load_pics () in
  Hashtbl.find_opt res_pics "DIFFS" |> Option.iter extend_menu_board;
  {res_maps; res_pics; res_cities}

module Dir = Engine.Dir
open Dir
let track_dirs =
  [[Up]; [UpRight]; [Right]; [DownRight]; [Down]; [DownLeft]; [Left]; [UpLeft];
  [Up; DownRight]; [Up; Down]; [Up; DownLeft]; [Down; UpRight]; [UpRight; DownLeft]; [Left; UpRight];
    [Right; DownLeft]; [Left; Right];
  [Right; UpLeft]; [Left; DownRight]; [UpLeft; DownRight]; [Down; UpLeft]; [Up; Down; DownRight];
    [Up; Down; DownLeft]; [Up; Down; UpRight]; [Up; Down; UpLeft]; [Left; Right; UpRight];
    [Left; Right; DownRight]; [Left; Right; UpLeft]; [Left; Right; DownLeft]; [Down; DownLeft; UpRight];
    [Left; DownLeft; UpRight]; [Up; UpLeft; DownRight]; [Left; UpLeft; DownRight];
  [Down; UpLeft; DownRight]; [Right; UpLeft; DownRight]; [Up; DownLeft; UpRight]; [Right; UpRight; DownLeft]]

  (* Only the computer can make these *)
let illegal_track =
  [[Up; Down; Left; Right]; [UpRight; DownRight; DownLeft; UpLeft]]

let track_turns =
  [[Up; Right]; [Down; Right]; [Down; Left]; [Up; Left]; [UpRight; DownRight]; [DownLeft; DownRight];
    [UpLeft; DownLeft]; [UpLeft; UpRight]]

  (* Dirs for non-track stuff *)
let straight_track =
  [[Dir.Up;Down]; [UpRight; DownLeft]; [Left;Right]; [UpLeft; DownRight]]

let soft_turns =
  [[Dir.Up; DownRight]; [Up; DownLeft];
    [Right; UpLeft]; [Right; DownLeft];
    [Down; UpLeft]; [Down; UpRight];
    [Left; UpRight]; [Left; DownRight]]
