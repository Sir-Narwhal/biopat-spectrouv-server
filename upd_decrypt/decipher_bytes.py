import struct

if __name__ == "__main__":  

    with open(".\\upd_decrypt\\udp_hexdump_1.txt", "rb") as f: 
        data = f.read()
        # f.readline()
        # f.readline() 
        # data = f.readline()

        data = data[32:]
        print(data) 
        print(len(data))
        vals = struct.unpack(f"<{int(240/4)}f", data[:240]) 

        print(vals)  