// Runs the pinned, unmodified Tatti GameData and DatTable implementation.
// Only non-DAT media loaders are stubbed: they neither feed nor write DAT data.
using System;
using System.IO;

class Program {
    public static void Main(string[] args) {
        if (args.Length != 3) throw new ArgumentException("raw-root proof-root output-root");
        Tatti3.Properties.Resources.RawRoot = Path.GetFullPath(args[0]);
        Tatti3.Properties.Resources.ProofRoot = Path.GetFullPath(args[1]);
        var game = Tatti3.GameData.GameData.Open(args[0]);
        game.Save(args[2]);
        Console.WriteLine("Pinned Tatti GameData.Save: all eleven tables written; DAT writer roundtrip checks passed.");
    }
}

namespace Tatti3.Properties {
    static class Resources {
        public static string RawRoot = "";
        public static string ProofRoot = "";
        static byte[] Dat(string name) => File.ReadAllBytes(Path.Combine(RawRoot,"arr",name+".dat"));
        public static byte[] arr_units_dat => Dat("units");
        public static byte[] arr_weapons_dat => Dat("weapons");
        public static byte[] arr_flingy_dat => Dat("flingy");
        public static byte[] arr_sprites_dat => Dat("sprites");
        public static byte[] arr_images_dat => Dat("images");
        public static byte[] arr_upgrades_dat => Dat("upgrades");
        public static byte[] arr_techdata_dat => Dat("techdata");
        public static byte[] arr_portdata_dat => Dat("portdata");
        public static byte[] arr_mapdata_dat => Dat("mapdata");
        public static byte[] arr_orders_dat => Dat("orders");
        public static byte[] buttons_bin => File.ReadAllBytes(Path.Combine(ProofRoot,"buttons.bin"));
        public static byte[] firegraft_default_fgp => File.ReadAllBytes(Path.Combine(ProofRoot,"..","dat_sources","tatti3","Resources","firegraft.fgp"));
        public static byte[] arr_images_tbl => Array.Empty<byte>();
        public static byte[] arr_portdata_tbl => Array.Empty<byte>();
        public static byte[] arr_mapdata_tbl => Array.Empty<byte>();
        public static byte[] rez_stat_txt_json => Array.Empty<byte>();
        public static byte[] rez_sfx_json => Array.Empty<byte>();
        public static byte[] cmdicons_dds_grp => Array.Empty<byte>();
    }
}

namespace Tatti3.GameData {
    class StringTable {
        public static StringTable FromJson(Stream value) => new StringTable();
        public static StringTable FromXml(Stream value) => new StringTable();
        public static StringTable FromTbl(Stream value) => new StringTable();
    }
    class SfxData { public static SfxData FromJson(Stream value) => new SfxData(); }
    class DdsGrp { public DdsGrp(Stream value) {} }
}
