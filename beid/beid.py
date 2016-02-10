import smartcard.System
from smartcard.pcsc.PCSCReader import PCSCReader

MAP_MOIS = {
    "JANV" : "01",
    "JAN"  : "01",
    "FEVR" : "02",
    "FEV"  : "02",
    "MARS" : "03",
    "MAR"  : "03",
    "AVRI" : "04",
    "AVR"  : "04",
    "MAI"  : "05",
    "JUIN" : "06",
    "JUIL" : "07",
    "AOUT" : "08",
    "AOU"  : "08",
    "SEPT" : "09",
    "SEP"  : "09",
    "OCTO" : "10",
    "OCT"  : "10",
    "NOVE" : "11",
    "NOV"  : "11",
    "DECE" : "12",
    "DEC"  : "12"
    }

ID = [0x3F, 0x00, 0xDF, 0x01, 0x40, 0x31]
ADDRESS = [0x3F, 0x00, 0xDF, 0x01, 0x40, 0x33]
PHOTO = [0x3F, 0x00, 0xDF, 0x01, 0x40, 0x35]

def scan_readers():
    r_list = smartcard.System.readers()
    return [BEID_reader(r) for r in r_list]

class BEID_reader(object):

    def __init__(self, b_rdr):
        if not isinstance(b_rdr, PCSCReader):
            raise TypeError("Argument should be an instance of" \
                            "smartcard.pcsc.PCSCReader.PCSCReader")
        self._reader = b_rdr
        self._cnx = b_rdr.createConnection()

    def read_card(self, read_photo = False):
        # TODO : manage exception
        self._cnx.connect()

        # select file : informations
        # TODO : manage return codes
        cmd = [0x00, 0xA4, 0x08, 0x0C, len(ID)] + ID        
        data, sw1, sw2 = self._sendADPU(cmd)

        # read file
        cmd = [0x00, 0xB0, 0x00, 0x00, 256]
        data, sw1, sw2 = self._sendADPU(cmd)
        if "%x"%sw1 == "6c":
            cmd = [0x00, 0xB0, 0x00, 0x00, sw2]
            data, sw1, sw2 = self._sendADPU(cmd)
            idx = 0
            num_info = 0
            infos = []
            while num_info <= 12:
                num_info = data[idx]
                idx += 1
                len_info = data[idx]
                idx += 1
                chaine_bytes = []
                for x in range(len_info):
                    chaine_bytes.append(data[idx])
                    idx += 1
                try:
                    infos.append(bytes(chaine_bytes).decode("utf-8"))
                except UnicodeDecodeError:
                    infos.append(u"")
            informations = {
        "num_carte" : infos[0],
        "date_debut" : infos[2].replace(".","/"),
        "date_fin" : infos[3].replace(".","/"),
        "lieu_delivrance" : infos[4],
        "num_nat" : infos[5],
        "nom" : infos[6],
        "prenoms" : infos[7],
        "suffixe" : infos[8],
        "nationalite" : infos[9],
        "lieu_naissance" : infos[10],
        "date_naissance" : infos[11].split()[0] + "/" + MAP_MOIS[infos[11].split()[1]] + "/" + infos[11].split()[2],
        "sexe" : infos[12],
        }

        # select file : adresse
        cmd = [0x00, 0xA4, 0x08, 0x0C, len(ADDRESS)] + ADDRESS
        data, sw1, sw2 = self._sendADPU(cmd)

        # read file
        cmd = [0x00, 0xB0, 0x00, 0x00, 256]
        data, sw1, sw2 = self._sendADPU(cmd)
        if "%x"%sw1 == "6c":
            cmd = [0x00, 0xB0, 0x00, 0x00, sw2]
            data, sw1, sw2 = self._sendADPU(cmd)
            idx = 0
            num_info = 0
            infos = []
            while num_info <= 2:
                num_info = data[idx]
                idx += 1
                len_info = data[idx]
                idx += 1
                chaine_bytes = []
                for x in range(len_info):
                    chaine_bytes.append(data[idx])
                    idx += 1
                try:
                    infos.append(bytes(chaine_bytes).decode("utf-8"))
                except UnicodeDecodeError:
                    infos.append(u"")

        informations["adresse"] = infos[0]
        informations["code_postal"] = infos[1]
        informations["localite"] = infos[2]
        
        if read_photo:
            # select file : photo
            cmd = [0x00, 0xA4, 0x08, 0x0C, len(PHOTO)] + PHOTO
            data, sw1, sw2 = self._sendADPU(cmd)

            photo_bytes = []

            offset = 0
            while "%x"%sw1 == "90":
                cmd = [0x00, 0xB0, offset, 0x00, 256]
                data, sw1, sw2 = self._sendADPU(cmd)
                photo_bytes += data
                offset += 1
            if "%x"%sw1 == "6c":
                offset -= 1
                cmd = [0x00, 0xB0, offset, 0x00, sw2]
                data, sw1, sw2 = self._sendADPU(cmd)
                photo_bytes += data
                
            photo = bytearray(photo_bytes)
            informations["photo"] = photo
        
        return informations

        

    def __repr__(self):
        return self._reader.name

    def _sendADPU(self, apdu):
        response, sw1, sw2 = self._cnx.transmit(apdu)
        return response, sw1, sw2
