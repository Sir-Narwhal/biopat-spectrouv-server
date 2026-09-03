# UDP Parser Service API

## Module: `parselibrary.udp_parser`

The UDP Parser service receives, validates, and decodes incoming 840-byte UDP spectral broadcast datagrams from the spectrometer.

### Functions

#### `unpack_udp(binary_string: bytes) -> List[float]`
Extracts the 201 float32 values from an incoming 840-byte datagram payload.

#### `collect_mpt_spectra(udp: socket.socket) -> Dict[str, List[float]]`
Reads datagrams from the UDP socket and maps tec5 packet type integers to spectral identifiers:
- Type 4 $ightarrow$ `sample` (Sample Intensity)
- Type 5 $ightarrow$ `onlinereference` (Reference Intensity)
- Type 7 $ightarrow$ `transmission`
- Type 9 $ightarrow$ `absorbance`
- Type 11 $ightarrow$ `calibration`
