
type t =
  | EastUS
  | WestUS
  | Britain
  | Europe
  | Netherlands (* NOT an original region: added by this remake. Must stay last: its index selects CITIES4.DTA *)
  [@@deriving enum, eq, yojson]

let regions = [EastUS; WestUS; Britain; Europe; Netherlands]

let show = function
  | EastUS -> "Eastern USA"
  | WestUS -> "Western USA"
  | Britain -> "England"
  | Europe -> "Europe"
  | Netherlands -> "Netherlands"

let start_year = function
  | EastUS -> 1830
  | WestUS -> 1866
  | Britain -> 1828
  | Europe -> 1900
  | Netherlands -> 1839 (* Amsterdam - Haarlem, the first Dutch railway *)

let money_symbol = function
  | EastUS | WestUS -> '$'
  | Britain | Europe -> '\\'
  | Netherlands -> 'f' (* guilder *)

let is_us = function
  | EastUS
  | WestUS -> true
  | Britain
  | Europe
  | Netherlands -> false

let is_east_us = function
  | EastUS -> true
  | _ -> false

let is_west_us = function
  | WestUS -> true
  | _ -> false

let is_europe = function
  | Europe -> true
  | _ -> false

  (* Handle larger scale of Europe map *)
let dist_mult = function
  | Europe -> 2
  | _ -> 1

  (* Avoid Money for circularity *)
let num_bonds region amount =
  let divide = match region with
    | WestUS -> 1000
    | _ -> 500
  in
  amount / divide

