import React, { useState, useMemo, useEffect } from 'react';
import { 
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, 
  ResponsiveContainer, BarChart, Bar, ScatterChart, Scatter, Legend, PieChart, Pie, Cell
} from 'recharts';
import { 
  MapPin, Home, DollarSign, TrendingUp, Info, LayoutDashboard, 
  List, ArrowUpRight, ArrowDownRight, RefreshCw, Sparkles, MessageCircle, X, Check,
  Map, MessageSquareMore, Copy, PaintBucket, Heart, Calculator, Compass,
  Users, Wallet, Baby, Star, Building, ShoppingBag, Utensils, Car, Clock, Eye, Database, Search, Circle,
  Train, GraduationCap, ShoppingCart, Coffee, Navigation, ExternalLink, Zap
} from 'lucide-react';

// --- COMPONENTS ---

const Card = ({ children, className = "" }) => (
  <div className={`bg-white rounded-xl shadow-sm border border-slate-200 p-5 ${className}`}>
    {children}
  </div>
);

const StatCard = ({ title, value, subtext, trend, icon: Icon, colorClass }) => (
  <Card>
    <div className="flex justify-between items-start mb-2">
      <div className={`p-2 rounded-lg ${colorClass} bg-opacity-10`}>
        <Icon className={`w-5 h-5 ${colorClass.replace('bg-', 'text-')}`} />
      </div>
      {trend !== undefined && (
        <span className={`flex items-center text-xs font-medium ${trend > 0 ? 'text-emerald-600' : 'text-red-600'}`}>
          {trend > 0 ? <ArrowUpRight className="w-3 h-3 mr-1" /> : <ArrowDownRight className="w-3 h-3 mr-1" />}
          {Math.abs(trend)}%
        </span>
      )}
    </div>
    <h3 className="text-slate-500 text-sm font-medium">{title}</h3>
    <p className="text-2xl font-bold text-slate-800 mt-1">{value}</p>
    {subtext && <p className="text-xs text-slate-400 mt-1">{subtext}</p>}
  </Card>
);

const formatCurrency = (val) => new Intl.NumberFormat('en-SG', { style: 'currency', currency: 'SGD', maximumFractionDigits: 0 }).format(val);

// --- API HELPERS ---

const RESALE_RESOURCE_ID = 'd_8b84c4ee58e3cfc0ece0d773c8ca6abc'; 
const PROPERTY_RESOURCE_ID = 'd_17f5382f26140b1fdae0ba2ef6239d2f';
const SCHOOL_RESOURCE_ID = 'd_688b934f82c1059ed0a6993d2a829089';

const parseLease = (leaseStr) => {
  if (typeof leaseStr === 'number') return leaseStr;
  if (!leaseStr) return 99;
  const parts = leaseStr.split(' ');
  const years = parseInt(parts[0]) || 0;
  return years;
};

// Address Normalizer
const normalizeStreet = (street) => {
  if (!street) return '';
  return street.toUpperCase()
    .replace(/\bAVENUE\b/g, 'AVE')
    .replace(/\bROAD\b/g, 'RD')
    .replace(/\bSTREET\b/g, 'ST')
    .replace(/\bCRESCENT\b/g, 'CRES')
    .replace(/\bDRIVE\b/g, 'DR')
    .replace(/\bJALAN\b/g, 'JLN')
    .replace(/\bLORONG\b/g, 'LOR')
    .replace(/\bUPPER\b/g, 'UPP')
    .replace(/\bBUKIT\b/g, 'BT')
    .replace(/\bKAMPONG\b/g, 'KG')
    .replace(/\bTANJONG\b/g, 'TG')
    .replace(/\bCENTRAL\b/g, 'CTRL')
    .trim();
};

const POSTAL_SECTOR_MAP = {
    '73': ['WOODLANDS'], '75': ['SEMBAWANG'], '76': ['YISHUN'], '79': ['SENGKANG', 'PUNGGOL'],
    '53': ['HOUGANG', 'SERANGOON'], '54': ['SENGKANG'], '55': ['SERANGOON'], '82': ['PUNGGOL'],
    '51': ['PASIR RIS'], '52': ['TAMPINES'], '46': ['BEDOK'], '47': ['BEDOK'], '48': ['BEDOK'],
    '60': ['JURONG EAST'], '61': ['JURONG WEST'], '62': ['JURONG WEST'], '64': ['JURONG WEST'],
    '65': ['BUKIT BATOK'], '66': ['BUKIT BATOK', 'BUKIT TIMAH'], '67': ['BUKIT PANJANG'], '68': ['CHOA CHU KANG'],
    '12': ['CLEMENTI'], '31': ['TOA PAYOH'], '56': ['ANG MO KIO'], '57': ['BISHAN', 'ANG MO KIO'],
    '14': ['QUEENSTOWN', 'BUKIT MERAH'], '15': ['BUKIT MERAH'], '10': ['BUKIT MERAH']
};

const getTargetTowns = (postal) => {
    if (!postal || postal.length < 2) return [];
    const sector = postal.substring(0, 2);
    return POSTAL_SECTOR_MAP[sector] || [];
};

// --- GEOSPATIAL HELPERS ---

const getDistanceFromLatLonInKm = (lat1, lon1, lat2, lon2) => {
  const R = 6371; 
  const dLat = deg2rad(lat2 - lat1);
  const dLon = deg2rad(lon2 - lon1);
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(deg2rad(lat1)) * Math.cos(deg2rad(lat2)) *
    Math.sin(dLon / 2) * Math.sin(dLon / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  const d = R * c; 
  return d;
}

const deg2rad = (deg) => {
  return deg * (Math.PI / 180)
}

// MRT STATIONS (Static fallback for speed & reliability)
const MRT_STATIONS = [
  { name: "Jurong East", lat: 1.333207, lng: 103.742308 }, { name: "Bukit Batok", lat: 1.349069, lng: 103.749596 },
  { name: "Bukit Gombak", lat: 1.359043, lng: 103.751863 }, { name: "Choa Chu Kang", lat: 1.385417, lng: 103.744316 },
  { name: "Yew Tee", lat: 1.397383, lng: 103.747523 }, { name: "Kranji", lat: 1.425178, lng: 103.762165 },
  { name: "Marsiling", lat: 1.432521, lng: 103.774074 }, { name: "Woodlands", lat: 1.436975, lng: 103.786400 },
  { name: "Admiralty", lat: 1.440585, lng: 103.800998 }, { name: "Sembawang", lat: 1.449050, lng: 103.820046 },
  { name: "Canberra", lat: 1.4430766, lng: 103.8297025 }, { name: "Yishun", lat: 1.429443, lng: 103.835005 },
  { name: "Khatib", lat: 1.417383, lng: 103.832980 }, { name: "Yio Chu Kang", lat: 1.381682, lng: 103.844993 },
  { name: "Ang Mo Kio", lat: 1.369933, lng: 103.849553 }, { name: "Bishan", lat: 1.350839, lng: 103.848144 },
  { name: "Toa Payoh", lat: 1.332597, lng: 103.847577 }, { name: "Novena", lat: 1.320441, lng: 103.843825 },
  { name: "Orchard", lat: 1.302422, lng: 103.835267 }, { name: "Pasir Ris", lat: 1.373045, lng: 103.949255 },
  { name: "Tampines", lat: 1.354825, lng: 103.943185 }, { name: "Simei", lat: 1.343197, lng: 103.953377 },
  { name: "Tanah Merah", lat: 1.327187, lng: 103.946396 }, { name: "Bedok", lat: 1.324021, lng: 103.930225 },
  { name: "Kembangan", lat: 1.321038, lng: 103.912949 }, { name: "Eunos", lat: 1.319778, lng: 103.903252 },
  { name: "Paya Lebar", lat: 1.318181, lng: 103.892388 }, { name: "Aljunied", lat: 1.316433, lng: 103.882893 },
  { name: "Kallang", lat: 1.311540, lng: 103.871337 }, { name: "Lavender", lat: 1.307363, lng: 103.862768 },
  { name: "Bugis", lat: 1.300465, lng: 103.855707 }, { name: "Tiong Bahru", lat: 1.286102, lng: 103.827019 },
  { name: "Redhill", lat: 1.289563, lng: 103.816817 }, { name: "Queenstown", lat: 1.294865, lng: 103.806077 },
  { name: "Commonwealth", lat: 1.302439, lng: 103.798312 }, { name: "Buona Vista", lat: 1.307349, lng: 103.790080 },
  { name: "Dover", lat: 1.311412, lng: 103.778651 }, { name: "Clementi", lat: 1.315027, lng: 103.765191 },
  { name: "Boon Lay", lat: 1.338602, lng: 103.706065 }, { name: "Pioneer", lat: 1.337581, lng: 103.697405 },
  { name: "Joo Koon", lat: 1.327708, lng: 103.678310 }, { name: "Serangoon", lat: 1.349706, lng: 103.873569 },
  { name: "Kovan", lat: 1.360180, lng: 103.885000 }, { name: "Hougang", lat: 1.371292, lng: 103.892380 },
  { name: "Buangkok", lat: 1.382877, lng: 103.893197 }, { name: "Sengkang", lat: 1.391695, lng: 103.895935 },
  { name: "Punggol", lat: 1.405257, lng: 103.902330 }
];

// --- GEMINI API INTEGRATION ---
const callGemini = async (prompt) => {
  const apiKey = ""; // Provided by system
  try {
    const response = await fetch(
      `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent?key=${apiKey}`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          contents: [{ parts: [{ text: prompt }] }],
        }),
      }
    );
    const data = await response.json();
    if (data.error) throw new Error(data.error.message);
    return data.candidates[0].content.parts[0].text;
  } catch (error) {
    console.error("Gemini API Error:", error);
    return "Sorry, our AI analyst is currently unavailable. Please try again later.";
  }
};

export default function SingaporeHousingDashboard() {
  const [rawData, setRawData] = useState([]);
  const [blockInfoMap, setBlockInfoMap] = useState({}); 
  const [schoolData, setSchoolData] = useState([]); 
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Inventory Loading State
  const [inventoryStatus, setInventoryStatus] = useState('Init'); 
  const [inventoryCount, setInventoryCount] = useState(0);
  
  // Lists
  const [availableTowns, setAvailableTowns] = useState([]);
  const [availableFlatTypes, setAvailableFlatTypes] = useState([]);

  // Filters
  const [selectedTown, setSelectedTown] = useState('PUNGGOL'); 
  const [selectedFlatType, setSelectedFlatType] = useState('4 ROOM');
  const [viewMode, setViewMode] = useState('dashboard');
  
  // Location Search State
  const [searchPostal, setSearchPostal] = useState('');
  const [searchRadius, setSearchRadius] = useState(1); 
  const [isGeoSearching, setIsGeoSearching] = useState(false);
  const [geoFilteredIds, setGeoFilteredIds] = useState(null); 
  const [locationCache, setLocationCache] = useState({}); 
  const [searchStatusMsg, setSearchStatusMsg] = useState('');

  // Amenities State
  const [amenitiesData, setAmenitiesData] = useState(null);
  const [amenitiesLoading, setAmenitiesLoading] = useState(false);
  const [selectedAmenity, setSelectedAmenity] = useState(null);

  // Persona State
  const [activePersona, setActivePersona] = useState(null);

  // Block X-Ray State
  const [selectedBlockData, setSelectedBlockData] = useState(null); 

  // AI State
  const [showAiModal, setShowAiModal] = useState(false);
  const [aiMode, setAiMode] = useState('insight'); 
  const [aiLoading, setAiLoading] = useState(false);
  const [aiResult, setAiResult] = useState('');
  
  // AI Input Forms
  const [ratingInput, setRatingInput] = useState({ price: '', size: '' });
  const [postalCode, setPostalCode] = useState('');
  const [renoInput, setRenoInput] = useState({ condition: 'Original', style: 'Minimalist' });
  const [vibeInput, setVibeInput] = useState('');
  const [grantInput, setGrantInput] = useState({ income: '', firstTimer: 'Yes', proximity: 'No' });
  const [fengShuiInput, setFengShuiInput] = useState({ facing: 'North-South', floor: 'High' });

  // --- PERSONA DEFINITIONS ---
  const PERSONAS = [
    {
        id: 'first_timer',
        label: 'First-Timer',
        icon: Star,
        targetType: '4 ROOM',
        color: 'bg-amber-100 text-amber-700 border-amber-200',
        tip: "💡 Pro Tip: Eligible for up to $80k in Enhanced Housing Grant (EHG). 4-Room is the most popular entry point."
    },
    {
        id: 'young_family',
        label: 'Young Family',
        icon: Baby,
        targetType: '5 ROOM',
        color: 'bg-pink-100 text-pink-700 border-pink-200',
        tip: "💡 Pro Tip: 5-Room offers future-proofing for growing kids. Check for proximity to Primary Schools (<1km)."
    },
    {
        id: 'big_family',
        label: 'Multi-Gen / Big Family',
        icon: Users,
        targetType: 'EXECUTIVE',
        color: 'bg-indigo-100 text-indigo-700 border-indigo-200',
        tip: "💡 Pro Tip: Look for Executive or 3Gen flats. Living near parents? You might get the Proximity Housing Grant (PHG)!"
    },
    {
        id: 'budget',
        label: 'Budget / Right-Sizer',
        icon: Wallet,
        targetType: '3 ROOM',
        color: 'bg-emerald-100 text-emerald-700 border-emerald-200',
        tip: "💡 Pro Tip: 3-Room flats offer great value. If you are >55, check if the Silver Housing Bonus applies."
    }
  ];

  const handlePersonaSelect = (persona) => {
      setActivePersona(persona.id);
      setSelectedFlatType(persona.targetType);
  };

  const processInventoryRecords = (records, currentMap) => {
      const newMap = { ...currentMap };
      records.forEach(record => {
          const key = `${normalizeStreet(record.street)}|${record.blk_no}`;
          newMap[key] = {
              totalUnits: parseInt(record.total_dwelling_units) || 0,
              yearCompleted: parseInt(record.year_completed) || 0,
              maxFloor: parseInt(record.max_floor_lvl) || 0,
              hasMarket: record.market_hawker === 'Y',
              hasCommercial: record.commercial === 'Y',
              hasMultistoreyCarpark: record.multistorey_carpark === 'Y',
              mix: [
                  { name: '1-Room', value: parseInt(record['1room_sold']) || 0 },
                  { name: '2-Room', value: parseInt(record['2room_sold']) || 0 },
                  { name: '3-Room', value: parseInt(record['3room_sold']) || 0 },
                  { name: '4-Room', value: parseInt(record['4room_sold']) || 0 },
                  { name: '5-Room', value: parseInt(record['5room_sold']) || 0 },
                  { name: 'Exec', value: parseInt(record['exec_sold']) || 0 },
              ].filter(x => x.value > 0)
          };
      });
      return newMap;
  };

  // --- AMENITIES SCANNER (FIXED FOR PROXIMITY) ---
  const fetchAmenities = async (targetLat, targetLng, postalCode) => {
      setAmenitiesLoading(true);
      setAmenitiesData(null);
      
      const results = {
          transport: [],
          schools: [],
          retail: [],
          groceries: []
      };

      try {
          // 1. MRT STATIONS
          const mrts = MRT_STATIONS.map(mrt => ({
              ...mrt,
              dist: getDistanceFromLatLonInKm(targetLat, targetLng, mrt.lat, mrt.lng)
          })).sort((a, b) => a.dist - b.dist).slice(0, 3);
          
          results.transport = mrts.map(m => ({
              name: `${m.name} MRT`,
              type: 'MRT',
              dist: `${m.dist.toFixed(2)} km`,
              lat: m.lat,
              lng: m.lng
          }));

          // 2. SCHOOLS
          if (schoolData.length > 0 && postalCode) {
              const sector = postalCode.substring(0, 2);
              const nearbySchools = schoolData.filter(s => 
                  s.postal_code && s.postal_code.toString().startsWith(sector.substring(0,1))
              );

              // Use OneMap to verify/geocode schools
              const verifiedSchools = [];
              // Check max 15 potential candidates
              const candidates = nearbySchools.slice(0, 15);

              for (const sch of candidates) {
                  try {
                      const res = await fetch(`https://www.onemap.gov.sg/api/common/elastic/search?searchVal=${sch.postal_code}&returnGeom=Y&getAddrDetails=N`);
                      const json = await res.json();
                      if (json.found > 0) {
                          const lat = parseFloat(json.results[0].LATITUDE);
                          const lng = parseFloat(json.results[0].LONGITUDE);
                          const dist = getDistanceFromLatLonInKm(targetLat, targetLng, lat, lng);
                          verifiedSchools.push({
                              name: sch.school_name,
                              type: 'School',
                              dist: `${dist.toFixed(2)} km`,
                              lat, lng, rawDist: dist
                          });
                      }
                  } catch (e) {}
              }
              results.schools = verifiedSchools.sort((a, b) => a.rawDist - b.rawDist).slice(0, 3);
          }

          // 3. MALLS & SUPERMARKETS (Proximity Search Fix)
          // Instruct AI to give specific names AND generic brands for fallback
          const prompt = `
            List 3 major shopping malls and 3 major supermarkets closest to GPS ${targetLat}, ${targetLng} (Postal ${postalCode}).
            Also include generic brands: "FairPrice", "Sheng Siong", "Cold Storage", "Giant", "Prime Supermarket".
            Return simple JSON: { "malls": ["Name"], "supermarkets": ["Name"] }
          `;
          
          const jsonStr = await callGemini(prompt);
          const candidates = JSON.parse(jsonStr.replace(/```json/g, '').replace(/```/g, '').trim());
          
          // Improved Verification: Find NEAREST match in list
          const verifyCandidates = async (names, type) => {
              const verified = [];
              for (const name of names) {
                  try {
                      const res = await fetch(`https://www.onemap.gov.sg/api/common/elastic/search?searchVal=${name}&returnGeom=Y&getAddrDetails=N`);
                      const json = await res.json();
                      if (json.found > 0) {
                          // Find the result closest to target
                          let bestMatch = null;
                          let minDist = Infinity;

                          json.results.forEach(res => {
                              const lat = parseFloat(res.LATITUDE);
                              const lng = parseFloat(res.LONGITUDE);
                              const dist = getDistanceFromLatLonInKm(targetLat, targetLng, lat, lng);
                              if (dist < minDist) {
                                  minDist = dist;
                                  bestMatch = { name: res.SEARCHVAL, type, dist: `${dist.toFixed(2)} km`, lat, lng, rawDist: dist };
                              }
                          });

                          if (bestMatch && minDist < 3.0) {
                              verified.push(bestMatch);
                          }
                      }
                  } catch (e) {}
              }
              // Deduplicate
              const unique = verified.filter((v,i,a)=>a.findIndex(t=>(t.name === v.name))===i);
              return unique.sort((a, b) => a.rawDist - b.rawDist).slice(0, 3);
          };

          results.retail = await verifyCandidates(candidates.malls || [], 'Mall');
          results.groceries = await verifyCandidates(candidates.supermarkets || [], 'Supermarket');

          setAmenitiesData(results);

      } catch (e) {
          console.error("Amenities processing failed", e);
      } finally {
          setAmenitiesLoading(false);
      }
  };

  // --- HANDLE AMENITY CLICK ---
  const handleAmenityClick = async (amenity) => {
      if (amenity.lat && amenity.lng) {
          // We search by name to get the X/Y for the map embed
          try {
             const res = await fetch(`https://www.onemap.gov.sg/api/common/elastic/search?searchVal=${amenity.name}&returnGeom=Y&getAddrDetails=N`);
             const json = await res.json();
             if (json.found > 0) {
                 const bestMatch = json.results[0];
                 setSelectedAmenity({
                     ...amenity,
                     x: bestMatch.X,
                     y: bestMatch.Y
                 });
             } else {
                 alert("Map preview unavailable for this location.");
             }
          } catch(e) { console.error(e) }
          return;
      }
  };

  // --- LOCATION SEARCH HANDLER ---
  const handleLocationSearch = async () => {
      if (!searchPostal || searchPostal.length < 6) {
          alert("Please enter a valid 6-digit postal code.");
          return;
      }
      setIsGeoSearching(true);
      setSearchStatusMsg('Decoding postal code...');
      setGeoFilteredIds(null); 
      setAmenitiesData(null); 
      setSelectedTown('All'); 

      const sector = searchPostal.substring(0, 2);
      const last3 = searchPostal.slice(-3);
      const inferredBlockNum = parseInt(last3).toString(); 
      const inferredTowns = POSTAL_SECTOR_MAP[sector] || [];
      
      let initialMatches = [];

      if (inferredTowns.length > 0) {
          const candidateIds = rawData.filter(d => {
              if (!inferredTowns.includes(d.town)) return false;
              const blockNum = d.block.replace(/\D/g, '');
              return blockNum === inferredBlockNum;
          }).map(d => d.id);

          if (candidateIds.length > 0) {
              setGeoFilteredIds(candidateIds);
              initialMatches = candidateIds;
              setSearchStatusMsg(`⚡ Instant Decoded: Sector ${sector} Blk ${inferredBlockNum}...`);
          }
      }

      try {
          const targetRes = await fetch(`https://www.onemap.gov.sg/api/common/elastic/search?searchVal=${searchPostal}&returnGeom=Y&getAddrDetails=Y`);
          const targetJson = await targetRes.json();
          
          if (targetJson.found === 0) {
              if (initialMatches.length > 0) {
                  setSearchStatusMsg('Location API unverified, but Block found in records.');
                  setIsGeoSearching(false);
                  return;
              }
              alert("Postal code not found in Singapore.");
              setIsGeoSearching(false);
              return;
          }

          const targetLat = parseFloat(targetJson.results[0].LATITUDE);
          const targetLng = parseFloat(targetJson.results[0].LONGITUDE);
          
          const candidateTowns = getTargetTowns(searchPostal);
          let candidateBlocks = [];
          if (candidateTowns.length > 0) {
              candidateBlocks = [...new Set(rawData.filter(item => candidateTowns.includes(item.town)).map(item => `${item.block} ${item.street}`))];
          } else {
              candidateBlocks = [...new Set(rawData.map(item => `${item.block} ${item.street}`))];
          }

          const newCache = { ...locationCache };
          const radiusMatches = [];
          const batchSize = 20; 
          
          const scanLimit = Math.min(candidateBlocks.length, 200); 
          
          for (let i = 0; i < scanLimit; i += batchSize) {
              const batch = candidateBlocks.slice(i, i + batchSize);
              const promises = batch.map(async (address) => {
                  if (newCache[address]) return { address, ...newCache[address] }; 
                  try {
                      const res = await fetch(`https://www.onemap.gov.sg/api/common/elastic/search?searchVal=${address}&returnGeom=Y&getAddrDetails=N`);
                      const json = await res.json();
                      if (json.found > 0) {
                          const lat = parseFloat(json.results[0].LATITUDE);
                          const lng = parseFloat(json.results[0].LONGITUDE);
                          newCache[address] = { lat, lng }; 
                          return { address, lat, lng };
                      }
                  } catch (e) {}
                  return null;
              });

              const results = await Promise.all(promises);
              
              results.forEach(res => {
                  if (res) {
                      const dist = getDistanceFromLatLonInKm(targetLat, targetLng, res.lat, res.lng);
                      if (dist <= searchRadius) {
                          const matchingTransactions = rawData.filter(
                              t => `${t.block} ${t.street}` === res.address
                          ).map(t => t.id);
                          radiusMatches.push(...matchingTransactions);
                      }
                  }
              });
              
              if (i % 50 === 0) setSearchStatusMsg(`Scanned ${i} blocks...`);
          }

          setLocationCache(newCache); 
          const finalMatches = [...new Set([...initialMatches, ...radiusMatches])];
          setGeoFilteredIds(finalMatches);
          
          fetchAmenities(targetLat, targetLng, searchPostal);

      } catch (err) {
          console.error(err);
          if (initialMatches.length > 0) setSearchStatusMsg('Radius search interrupted. Showing exact block match.');
          else alert("Location search failed.");
      } finally {
          setIsGeoSearching(false);
          setSearchStatusMsg('');
      }
  };

  const clearLocationSearch = () => {
      setSearchPostal('');
      setGeoFilteredIds(null);
      setAmenitiesData(null);
  };

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      
      try {
        const resaleRes = await fetch(
          `https://data.gov.sg/api/action/datastore_search?resource_id=${RESALE_RESOURCE_ID}&limit=3000&sort=month desc`
        );
        const resaleJson = await resaleRes.json();
        if (resaleJson.success) {
            const records = resaleJson.result.records.map((r, i) => ({
              id: i,
              month: r.month,
              town: r.town,
              flatType: r.flat_type,
              block: r.block,
              street: r.street_name,
              floorArea: parseFloat(r.floor_area_sqm),
              price: parseFloat(r.resale_price),
              leaseLeft: parseLease(r.remaining_lease),
              storey: r.storey_range,
              psf: Math.round(parseFloat(r.resale_price) / (parseFloat(r.floor_area_sqm) * 10.764))
            }));
            setRawData(records);
            const towns = [...new Set(records.map(r => r.town))].sort();
            const types = [...new Set(records.map(r => r.flatType))].sort();
            setAvailableTowns(towns);
            setAvailableFlatTypes(types);
        }
      } catch (err) { console.error(err); setError("Failed to load transactions."); } 
      finally { setLoading(false); }

      try {
          const schoolRes = await fetch(`https://data.gov.sg/api/action/datastore_search?resource_id=${SCHOOL_RESOURCE_ID}&limit=500`);
          const schoolJson = await schoolRes.json();
          if (schoolJson.success) {
              setSchoolData(schoolJson.result.records);
          }
      } catch (e) { console.error("School data fetch failed", e); }

      setInventoryStatus('Loading');
      let offset = 0; let limit = 2000; let totalFetched = 0; let tempMap = {}; let keepFetching = true;
      try {
          while (keepFetching && totalFetched < 15000) { 
              const invUrl = `https://data.gov.sg/api/action/datastore_search?resource_id=${PROPERTY_RESOURCE_ID}&limit=${limit}&offset=${offset}`;
              const invRes = await fetch(invUrl);
              const invJson = await invRes.json();
              if (invJson.success && invJson.result.records.length > 0) {
                  const newRecords = invJson.result.records;
                  tempMap = processInventoryRecords(newRecords, tempMap);
                  totalFetched += newRecords.length;
                  setInventoryCount(totalFetched);
                  setBlockInfoMap(prev => ({...prev, ...tempMap}));
                  if (newRecords.length < limit) keepFetching = false; else offset += limit;
              } else { keepFetching = false; }
          }
          setInventoryStatus('Complete');
      } catch (invErr) { setInventoryStatus('Error'); }
    };

    fetchData();
  }, []);

  // --- DERIVED DATA ---
  
  const filteredData = useMemo(() => {
    let data = rawData;
    if (geoFilteredIds !== null) {
        data = data.filter(d => geoFilteredIds.includes(d.id));
    } else {
        if (selectedTown !== 'All') {
            data = data.filter(d => d.town === selectedTown);
        }
    }
    if (selectedFlatType !== 'All') {
        data = data.filter(d => d.flatType === selectedFlatType);
    }
    return data;
  }, [rawData, selectedTown, selectedFlatType, geoFilteredIds]);

  const stats = useMemo(() => {
    if (filteredData.length === 0) return { avgPrice: 0, minPrice: 0, maxPrice: 0, count: 0, avgPsf: 0, trend: 0, avgSize: 0 };
    
    const prices = filteredData.map(d => d.price);
    const psfs = filteredData.map(d => d.psf);
    const sizes = filteredData.map(d => d.floorArea);
    const total = prices.reduce((a, b) => a + b, 0);
    const totalPsf = psfs.reduce((a, b) => a + b, 0);
    const totalSize = sizes.reduce((a, b) => a + b, 0);

    return {
      avgPrice: Math.round(total / prices.length),
      minPrice: Math.min(...prices),
      maxPrice: Math.max(...prices),
      count: prices.length,
      avgPsf: Math.round(totalPsf / psfs.length),
      avgSize: Math.round(totalSize / sizes.length),
    };
  }, [filteredData]);

  const chartData = useMemo(() => {
    const grouped = {};
    filteredData.forEach(d => {
      if (!grouped[d.month]) grouped[d.month] = { month: d.month, total: 0, count: 0, totalPsf: 0 };
      grouped[d.month].total += d.price;
      grouped[d.month].totalPsf += d.psf;
      grouped[d.month].count += 1;
    });
    
    return Object.values(grouped)
      .map(g => ({
        month: g.month,
        avgPrice: Math.round(g.total / g.count),
        avgPsf: Math.round(g.totalPsf / g.count),
        count: g.count
      }))
      .sort((a, b) => a.month.localeCompare(b.month)); 
  }, [filteredData]);

  const trendPercentage = useMemo(() => {
    if (chartData.length < 2) return 0;
    const first = chartData[0].avgPrice;
    const last = chartData[chartData.length - 1].avgPrice;
    return ((last - first) / first * 100).toFixed(1);
  }, [chartData]);


  // --- AI HANDLERS ---
  const handleAiAnalysis = async () => {
    setAiLoading(true); setAiResult('');
    const prompt = `Act as a Singapore Property Analyst expert. Context: The user is looking at REAL HDB resale data for ${selectedTown} (${selectedFlatType}). Market Data: Average Price: $${stats.avgPrice}, Trend: ${trendPercentage}%. Provide a concise market insight (max 100 words).`;
    const result = await callGemini(prompt);
    setAiResult(result); setAiLoading(false);
  };

  const handleAiRating = async () => {
    if (!ratingInput.price || !ratingInput.size) return;
    setAiLoading(true); setAiResult('');
    const userPsf = Math.round(parseInt(ratingInput.price) / (parseInt(ratingInput.size) * 10.764));
    const prompt = `Act as a strict property valuation expert. Market Benchmark: Avg PSF $${stats.avgPsf}. User Listing: $${ratingInput.price}, ${userPsf} psf. Verdict: Undervalued, Fair, or Overpriced?`;
    const result = await callGemini(prompt);
    setAiResult(result); setAiLoading(false);
  };

  const handleAiLocation = async () => {
    setAiLoading(true); setAiResult('');
    let prompt = postalCode && postalCode.length >= 6 
      ? `Analyze Singapore Postal Code ${postalCode} in ${selectedTown}. 3 points: Connectivity (MRT), Amenities, Future Value.`
      : `Analyze ${selectedTown}. 3 points: Connectivity, Amenities, Future Value.`;
    const result = await callGemini(prompt);
    setAiResult(result); setAiLoading(false);
  };

  const handleAiNegotiate = async () => {
    setAiLoading(true); setAiResult('');
    const prompt = `Draft a WhatsApp negotiation message for a ${selectedFlatType} in ${selectedTown}. Market avg: ${formatCurrency(stats.avgPrice)}. Be polite but firm.`;
    const result = await callGemini(prompt);
    setAiResult(result); setAiLoading(false);
  };

  const handleAiRenovation = async () => {
    setAiLoading(true); setAiResult('');
    const prompt = `Renovation budget for Singapore HDB ${selectedFlatType} (${stats.avgSize}sqm). Condition: ${renoInput.condition}. Style: ${renoInput.style}. Give Range and Breakdown.`;
    const result = await callGemini(prompt);
    setAiResult(result); setAiLoading(false);
  };

  const handleAiVibe = async () => {
    if (!vibeInput) return;
    setAiLoading(true); setAiResult('');
    const prompt = `Singapore Neighborhood match. User likes: "${vibeInput}". Town: ${selectedTown}. Rate 1-10 and suggest spots.`;
    const result = await callGemini(prompt);
    setAiResult(result); setAiLoading(false);
  };

  const handleAiGrant = async () => {
    setAiLoading(true); setAiResult('');
    const prompt = `Singapore HDB Grant estimator. Income: $${grantInput.income}. First Timer: ${grantInput.firstTimer}. Near Parents: ${grantInput.proximity}. Buying: ${selectedFlatType}. List eligible grants.`;
    const result = await callGemini(prompt);
    setAiResult(result); setAiLoading(false);
  };

  const handleAiFengShui = async () => {
    setAiLoading(true); setAiResult('');
    const prompt = `Feng Shui analysis for Singapore HDB. Facing: ${fengShuiInput.facing}. Floor: ${fengShuiInput.floor}. Analyze Sun/Wind and Luck.`;
    const result = await callGemini(prompt);
    setAiResult(result); setAiLoading(false);
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
  };

  const getBlockInfo = (street, block) => {
      const key = `${normalizeStreet(street)}|${block}`;
      return blockInfoMap[key];
  }

  const getBlockBadges = (street, block) => {
      const info = getBlockInfo(street, block);
      if (!info) return null;

      return (
          <div className="flex flex-wrap gap-1 mt-1">
              {info.hasMarket && (
                  <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium bg-orange-100 text-orange-800" title="Market/Hawker in Block">
                      <Utensils className="w-3 h-3 mr-1" /> Hawker
                  </span>
              )}
              {info.hasCommercial && (
                  <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium bg-blue-100 text-blue-800" title="Shops in Block">
                      <ShoppingBag className="w-3 h-3 mr-1" /> Shops
                  </span>
              )}
              {info.totalUnits > 0 && (
                  <span className={`inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium ${info.totalUnits < 100 ? 'bg-purple-100 text-purple-800' : 'bg-slate-100 text-slate-600'}`}>
                      <Building className="w-3 h-3 mr-1" /> {info.totalUnits < 100 ? 'Low Density' : `${info.totalUnits} Units`}
                  </span>
              )}
          </div>
      );
  };

  const openBlockXRay = (transaction) => {
      const info = getBlockInfo(transaction.street, transaction.block);
      if (info) {
          setSelectedBlockData({ ...info, ...transaction });
      } else {
          setSelectedBlockData({ 
              ...transaction, 
              totalUnits: 'N/A', yearCompleted: 'N/A', mix: [] 
          });
      }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-slate-50">
        <div className="text-center">
          <RefreshCw className="w-10 h-10 text-blue-600 animate-spin mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-slate-700">Connecting to data.gov.sg...</h2>
          <p className="text-slate-500">Fetching latest live resale & property transactions.</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-slate-50">
         <div className="text-center p-8 bg-white rounded-xl shadow-lg border border-red-100 max-w-md">
            <div className="bg-red-50 text-red-500 p-3 rounded-full inline-block mb-4">
              <RefreshCw className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold text-slate-800 mb-2">Connection Issue</h3>
            <p className="text-slate-500 mb-4">{error}</p>
            <button onClick={() => window.location.reload()} className="px-4 py-2 bg-slate-900 text-white rounded-lg text-sm font-medium">Retry</button>
         </div>
      </div>
    );
  }

  const COLORS = ['#8884d8', '#82ca9d', '#ffc658', '#ff8042', '#0088FE', '#00C49F'];

  return (
    <div className="min-h-screen bg-slate-50 text-slate-800 font-sans relative">
      {/* HEADER */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-30">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="bg-blue-600 p-2 rounded-lg">
              <TrendingUp className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-slate-900 tracking-tight">SG HomeTrends</h1>
              <div className="flex items-center gap-1.5">
                <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></div>
                <p className="text-xs text-slate-500 font-medium">Live Data (Jan 2017+)</p>
              </div>
            </div>
          </div>
          <div className="flex gap-3">
             <button 
                onClick={() => setViewMode('dashboard')}
                className={`px-3 py-2 text-sm font-medium rounded-lg flex items-center gap-2 transition-colors ${viewMode === 'dashboard' ? 'bg-blue-50 text-blue-700' : 'text-slate-600 hover:bg-slate-100'}`}
              >
                <LayoutDashboard className="w-4 h-4" />
                <span className="hidden sm:inline">Dashboard</span>
             </button>
             <button 
                onClick={() => setViewMode('list')}
                className={`px-3 py-2 text-sm font-medium rounded-lg flex items-center gap-2 transition-colors ${viewMode === 'list' ? 'bg-blue-50 text-blue-700' : 'text-slate-600 hover:bg-slate-100'}`}
              >
                <List className="w-4 h-4" />
                <span className="hidden sm:inline">Transactions</span>
             </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 pb-24">
        
        {/* BUYER PERSONA SELECTOR */}
        <div className="mb-6">
            <h2 className="text-sm font-semibold text-slate-500 uppercase tracking-wider mb-3">Identify yourself as:</h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {PERSONAS.map(p => {
                    const Icon = p.icon;
                    const isActive = activePersona === p.id;
                    return (
                        <button
                            key={p.id}
                            onClick={() => handlePersonaSelect(p)}
                            className={`p-3 rounded-xl border flex items-center gap-3 transition-all ${isActive ? p.color + ' ring-2 ring-offset-1 ring-blue-500' : 'bg-white border-slate-200 hover:border-blue-300 hover:shadow-md text-slate-600'}`}
                        >
                            <div className={`p-2 rounded-lg bg-white bg-opacity-60`}>
                                <Icon className="w-5 h-5" />
                            </div>
                            <div className="text-left">
                                <div className="text-xs font-bold">{p.label}</div>
                                <div className="text-[10px] opacity-80">{p.targetType}</div>
                            </div>
                        </button>
                    )
                })}
            </div>
            {activePersona && (
                <div className="mt-3 p-3 bg-blue-50 border border-blue-100 rounded-lg text-sm text-blue-800 flex items-start gap-2 animate-in fade-in slide-in-from-top-2">
                    <Info className="w-4 h-4 mt-0.5 shrink-0" />
                    <span>{PERSONAS.find(p => p.id === activePersona).tip}</span>
                </div>
            )}
        </div>

        {/* LOCATION SEARCH SECTION */}
        <div className="bg-gradient-to-r from-violet-50 to-indigo-50 border border-violet-100 rounded-xl p-4 mb-6 relative overflow-hidden">
            <div className="absolute top-0 right-0 p-4 opacity-10">
                <Zap className="w-32 h-32 text-violet-300" />
            </div>
            <div className="relative z-10">
                {/* Search Bar Row */}
                <div className="flex flex-col md:flex-row gap-4 items-center">
                    <div className="flex-1 w-full">
                        <label className="block text-xs font-semibold text-violet-700 uppercase tracking-wider mb-1.5 flex items-center gap-1">
                            <Map className="w-3 h-3" /> Search Near Location (Smart Filter Active ⚡)
                        </label>
                        <div className="flex gap-2">
                            <div className="relative flex-1">
                                <input 
                                    type="text" 
                                    value={searchPostal}
                                    onChange={(e) => setSearchPostal(e.target.value)}
                                    placeholder="Enter Postal Code (e.g. 560123)"
                                    className="w-full pl-3 pr-3 py-2.5 bg-white border border-violet-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-violet-500"
                                    maxLength={6}
                                />
                            </div>
                            <div className="relative w-32">
                                <select 
                                    value={searchRadius}
                                    onChange={(e) => setSearchRadius(parseFloat(e.target.value))}
                                    className="w-full px-3 py-2.5 bg-white border border-violet-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-violet-500 appearance-none"
                                >
                                    <option value="0.5">500m</option>
                                    <option value="1">1km</option>
                                    <option value="2">2km</option>
                                </select>
                                <Circle className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
                            </div>
                            <button 
                                onClick={handleLocationSearch}
                                disabled={isGeoSearching || !searchPostal}
                                className="bg-violet-600 hover:bg-violet-700 text-white px-4 py-2 rounded-lg text-sm font-semibold flex items-center gap-2 disabled:bg-slate-300 transition-colors"
                            >
                                {isGeoSearching ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
                                Search
                            </button>
                            {geoFilteredIds && (
                                <button 
                                    onClick={clearLocationSearch}
                                    className="bg-white border border-slate-200 text-slate-600 hover:bg-slate-50 px-3 py-2 rounded-lg"
                                    title="Clear Search"
                                >
                                    <X className="w-4 h-4" />
                                </button>
                            )}
                        </div>
                    </div>
                </div>

                {/* Status Messages */}
                {searchStatusMsg && (
                    <p className="text-xs text-violet-600 mt-2 animate-pulse font-medium">{searchStatusMsg}</p>
                )}
                {geoFilteredIds && geoFilteredIds.length === 0 && !isGeoSearching && (
                    <p className="text-xs text-red-500 mt-2 font-medium">No recent transactions found within {searchRadius}km.</p>
                )}

                {/* Neighborhood Radar (Amenities) */}
                {amenitiesLoading && (
                    <div className="mt-4 p-4 bg-white/50 rounded-lg border border-violet-100 flex items-center justify-center gap-2">
                        <RefreshCw className="w-4 h-4 text-violet-500 animate-spin" />
                        <span className="text-sm text-violet-700 font-medium">Scanning neighborhood amenities...</span>
                    </div>
                )}

                {amenitiesData && !amenitiesLoading && (
                    <div className="mt-6 animate-in fade-in slide-in-from-top-2">
                        <h3 className="text-sm font-bold text-violet-800 mb-3 flex items-center gap-2">
                            <Compass className="w-4 h-4" /> Neighborhood Radar (Approx.)
                        </h3>
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
                            {/* Transport */}
                            <div className="bg-white p-3 rounded-lg border border-violet-100 shadow-sm">
                                <div className="flex items-center gap-2 text-violet-600 mb-2 font-semibold text-xs uppercase tracking-wide">
                                    <Train className="w-3 h-3" /> Transport
                                </div>
                                <div className="space-y-2">
                                    {amenitiesData.transport?.map((item, i) => (
                                        <div key={i} onClick={() => handleAmenityClick(item)} className="flex justify-between items-center text-sm cursor-pointer hover:bg-violet-50 p-1 rounded transition-colors group">
                                            <span className="font-medium text-slate-700 truncate group-hover:text-violet-700">{item.name}</span>
                                            <span className="text-xs text-slate-400 whitespace-nowrap bg-slate-50 px-1.5 py-0.5 rounded">{item.dist}</span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                            {/* Schools */}
                            <div className="bg-white p-3 rounded-lg border border-pink-100 shadow-sm">
                                <div className="flex items-center gap-2 text-pink-600 mb-2 font-semibold text-xs uppercase tracking-wide">
                                    <GraduationCap className="w-3 h-3" /> Education
                                </div>
                                <div className="space-y-2">
                                    {amenitiesData.schools?.map((item, i) => (
                                        <div key={i} onClick={() => handleAmenityClick(item)} className="flex justify-between items-center text-sm cursor-pointer hover:bg-pink-50 p-1 rounded transition-colors group">
                                            <span className="font-medium text-slate-700 truncate group-hover:text-pink-700">{item.name}</span>
                                            <span className="text-xs text-slate-400 whitespace-nowrap bg-slate-50 px-1.5 py-0.5 rounded">{item.dist}</span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                            {/* Retail */}
                            <div className="bg-white p-3 rounded-lg border border-blue-100 shadow-sm">
                                <div className="flex items-center gap-2 text-blue-600 mb-2 font-semibold text-xs uppercase tracking-wide">
                                    <ShoppingBag className="w-3 h-3" /> Lifestyle
                                </div>
                                <div className="space-y-2">
                                    {amenitiesData.retail?.map((item, i) => (
                                        <div key={i} onClick={() => handleAmenityClick(item)} className="flex justify-between items-center text-sm cursor-pointer hover:bg-blue-50 p-1 rounded transition-colors group">
                                            <span className="font-medium text-slate-700 truncate group-hover:text-blue-700">{item.name}</span>
                                            <span className="text-xs text-slate-400 whitespace-nowrap bg-slate-50 px-1.5 py-0.5 rounded">{item.dist}</span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                            {/* Groceries */}
                            <div className="bg-white p-3 rounded-lg border border-emerald-100 shadow-sm">
                                <div className="flex items-center gap-2 text-emerald-600 mb-2 font-semibold text-xs uppercase tracking-wide">
                                    <ShoppingCart className="w-3 h-3" /> Groceries
                                </div>
                                <div className="space-y-2">
                                    {amenitiesData.groceries?.map((item, i) => (
                                        <div key={i} onClick={() => handleAmenityClick(item)} className="flex justify-between items-center text-sm cursor-pointer hover:bg-emerald-50 p-1 rounded transition-colors group">
                                            <span className="font-medium text-slate-700 truncate group-hover:text-emerald-700">{item.name}</span>
                                            <span className="text-xs text-slate-400 whitespace-nowrap bg-slate-50 px-1.5 py-0.5 rounded">{item.dist}</span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>

        {/* FILTERS */}
        <div className={`bg-white rounded-xl shadow-sm border border-slate-200 p-4 mb-8 transition-opacity ${geoFilteredIds ? 'opacity-50 pointer-events-none' : 'opacity-100'}`}>
          <div className="flex flex-col md:flex-row gap-4 items-end md:items-center">
            
            <div className="flex-1 w-full">
              <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1.5 ml-1">Town / Estate</label>
              <div className="relative">
                <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                <select 
                  className="w-full pl-9 pr-4 py-2.5 bg-slate-50 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent appearance-none"
                  value={selectedTown}
                  onChange={(e) => { setSelectedTown(e.target.value); setAiResult(''); }}
                >
                  <option value="All">All Towns (Overview)</option>
                  {availableTowns.map(t => <option key={t} value={t}>{t}</option>)}
                </select>
              </div>
            </div>

            <div className="flex-1 w-full">
              <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1.5 ml-1">Flat Type</label>
              <div className="relative">
                <Home className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                <select 
                  className="w-full pl-9 pr-4 py-2.5 bg-slate-50 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent appearance-none"
                  value={selectedFlatType}
                  onChange={(e) => { setSelectedFlatType(e.target.value); setAiResult(''); }}
                >
                  <option value="All">All Types</option>
                  {availableFlatTypes.map(f => <option key={f} value={f}>{f}</option>)}
                </select>
              </div>
            </div>

            <div className="hidden md:block">
              <div className="bg-blue-50 text-blue-800 text-xs px-3 py-2 rounded-lg font-medium border border-blue-100 flex items-center gap-2">
                <Info className="w-3 h-3" />
                <span>Comparing {filteredData.length} records</span>
              </div>
            </div>

          </div>
        </div>

        {viewMode === 'dashboard' ? (
          <div className="space-y-6">
            
            {/* STATS GRID */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <StatCard 
                title="Avg Transacted Price" 
                value={formatCurrency(stats.avgPrice)} 
                subtext={`Based on ${stats.count} transactions`}
                trend={parseFloat(trendPercentage)} 
                icon={DollarSign} 
                colorClass="bg-emerald-500 text-emerald-600"
              />
               <StatCard 
                title="Avg PSF" 
                value={`$${stats.avgPsf} psf`} 
                subtext="Per Square Foot"
                trend={parseFloat(trendPercentage)/2} 
                icon={TrendingUp} 
                colorClass="bg-blue-500 text-blue-600"
              />
              <StatCard 
                title="Lowest Transacted" 
                value={formatCurrency(stats.minPrice)} 
                subtext="Best value in selection"
                icon={ArrowDownRight} 
                colorClass="bg-indigo-500 text-indigo-600"
              />
              <StatCard 
                title="Highest Transacted" 
                value={formatCurrency(stats.maxPrice)} 
                subtext="Premium units in selection"
                icon={ArrowUpRight} 
                colorClass="bg-orange-500 text-orange-600"
              />
            </div>

            {/* CHARTS ROW 1 */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <Card className="lg:col-span-2">
                <div className="flex justify-between items-center mb-6">
                  <div>
                    <h3 className="text-lg font-bold text-slate-800">Price Trend (Last 24 Months)</h3>
                    <p className="text-sm text-slate-500">Average resale price movement for {selectedTown === 'All' ? 'Singapore' : selectedTown}</p>
                  </div>
                </div>
                <div className="h-72 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={chartData}>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                      <XAxis 
                        dataKey="month" 
                        tick={{fontSize: 12, fill: '#64748b'}} 
                        axisLine={false} 
                        tickLine={false} 
                        tickMargin={10}
                        minTickGap={30}
                      />
                      <YAxis 
                        tick={{fontSize: 12, fill: '#64748b'}} 
                        axisLine={false} 
                        tickLine={false} 
                        tickFormatter={(val) => `$${val/1000}k`}
                        domain={['auto', 'auto']}
                      />
                      <RechartsTooltip 
                        contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                        formatter={(val) => formatCurrency(val)}
                      />
                      <Line 
                        type="monotone" 
                        dataKey="avgPrice" 
                        stroke="#3b82f6" 
                        strokeWidth={3} 
                        dot={{ r: 3, fill: '#3b82f6', strokeWidth: 0 }} 
                        activeDot={{ r: 6 }} 
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </Card>

              <Card>
                <h3 className="text-lg font-bold text-slate-800 mb-2">Volume Analysis</h3>
                <p className="text-sm text-slate-500 mb-6">Number of units sold per month</p>
                <div className="h-72 w-full">
                   <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={chartData}>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                      <XAxis hide dataKey="month" />
                      <YAxis tick={{fontSize: 12}} axisLine={false} tickLine={false} />
                      <RechartsTooltip cursor={{fill: '#f1f5f9'}} />
                      <Bar dataKey="count" fill="#94a3b8" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </Card>
            </div>

            {/* CHARTS ROW 2: Scatter Plot for Value Hunting */}
            <Card>
              <div className="flex justify-between items-center mb-6">
                <div>
                  <h3 className="text-lg font-bold text-slate-800">Price vs. Floor Area</h3>
                  <p className="text-sm text-slate-500">Spot good deals: Look for dots lower and to the right (Larger size, Lower Price)</p>
                </div>
                <div className="bg-slate-100 rounded-lg p-1 flex text-xs font-medium">
                  <div className="px-3 py-1 bg-white shadow-sm rounded-md text-slate-800">By Unit</div>
                </div>
              </div>
              <div className="h-80 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                    <XAxis 
                      type="number" 
                      dataKey="floorArea" 
                      name="Size" 
                      unit=" sqm" 
                      tick={{fontSize: 12}}
                      domain={['auto', 'auto']}
                    />
                    <YAxis 
                      type="number" 
                      dataKey="price" 
                      name="Price" 
                      tick={{fontSize: 12}} 
                      tickFormatter={(val) => `$${val/1000}k`}
                      domain={['auto', 'auto']}
                    />
                    <RechartsTooltip 
                      cursor={{ strokeDasharray: '3 3' }} 
                      content={({ active, payload }) => {
                        if (active && payload && payload.length) {
                          const data = payload[0].payload;
                          return (
                            <div className="bg-white p-3 shadow-lg rounded-lg border border-slate-100">
                              <p className="font-bold text-slate-800">{data.town}</p>
                              <p className="text-sm text-slate-600">{data.flatType} • {data.floorArea} sqm</p>
                              <p className="text-sm font-semibold text-blue-600 mt-1">{formatCurrency(data.price)}</p>
                              <p className="text-xs text-slate-400 mt-1">Lease: {data.leaseLeft} years</p>
                            </div>
                          );
                        }
                        return null;
                      }}
                    />
                    <Scatter name="Transactions" data={filteredData} fill="#8884d8">
                      {filteredData.map((entry, index) => (
                         <circle key={`cell-${index}`} cx="0" cy="0" r="4" fill={entry.leaseLeft < 60 ? '#f59e0b' : '#3b82f6'} fillOpacity={0.6} />
                      ))}
                    </Scatter>
                    <Legend 
                      verticalAlign="top" 
                      height={36}
                      payload={[
                        { value: 'Standard Lease (>60y)', type: 'circle', color: '#3b82f6' },
                        { value: 'Older Lease (<60y)', type: 'circle', color: '#f59e0b' }
                      ]}
                    />
                  </ScatterChart>
                </ResponsiveContainer>
              </div>
            </Card>

          </div>
        ) : (
          /* LIST VIEW */
          <Card className="overflow-hidden p-0">
             <div className="px-6 py-4 border-b border-slate-100 bg-slate-50 flex justify-between items-center">
               <h3 className="font-bold text-slate-700">Detailed Transaction History</h3>
               <span className="text-xs text-slate-500">Click any row to see <strong>Block X-Ray</strong></span>
             </div>
             <div className="overflow-x-auto">
               <table className="w-full text-left text-sm text-slate-600">
                 <thead className="bg-slate-50 text-xs uppercase font-semibold text-slate-500">
                   <tr>
                     <th className="px-6 py-3">Date</th>
                     <th className="px-6 py-3">Town / Block</th>
                     <th className="px-6 py-3">Details</th>
                     <th className="px-6 py-3">Storey</th>
                     <th className="px-6 py-3 text-right">Price</th>
                     <th className="px-6 py-3 text-right">PSF</th>
                   </tr>
                 </thead>
                 <tbody className="divide-y divide-slate-100">
                   {filteredData.slice(0, 50).map((item) => (
                     <tr key={item.id} onClick={() => openBlockXRay(item)} className="hover:bg-blue-50 transition-colors cursor-pointer group">
                       <td className="px-6 py-4 font-medium text-slate-800">{item.month}</td>
                       <td className="px-6 py-4">
                         <div className="font-semibold text-slate-800 group-hover:text-blue-700">{item.town}</div>
                         <div className="text-xs text-slate-500 group-hover:text-blue-600">Blk {item.block} {item.street}</div>
                         {/* BLOCK INFO BADGES */}
                         {getBlockBadges(item.street, item.block)}
                       </td>
                       <td className="px-6 py-4">
                         <div>{item.flatType}</div>
                         <div className="text-xs text-slate-500">{item.floorArea} sqm • {item.leaseLeft}y lease</div>
                       </td>
                       <td className="px-6 py-4">{item.storey}</td>
                       <td className="px-6 py-4 text-right font-bold text-slate-800">{formatCurrency(item.price)}</td>
                       <td className="px-6 py-4 text-right text-slate-500">${item.psf} psf</td>
                     </tr>
                   ))}
                 </tbody>
               </table>
               {filteredData.length > 50 && (
                 <div className="p-4 text-center text-sm text-slate-500 bg-slate-50 border-t border-slate-100">
                   Showing recent 50 of {filteredData.length} transactions
                 </div>
               )}
             </div>
          </Card>
        )}
      </main>

      {/* FOOTER DEBUG INFO */}
      <div className="fixed bottom-2 left-2 z-50 pointer-events-none">
        <div className="bg-white/90 backdrop-blur border border-slate-200 shadow-sm rounded-md px-2 py-1 flex items-center gap-2">
            {inventoryStatus === 'Error' ? (
                <>
                    <div className="w-2 h-2 rounded-full bg-red-500"></div>
                    <span className="text-[10px] text-red-500 font-medium">Inventory Failed (Showing Basic)</span>
                </>
            ) : (
                <>
                    <div className={`w-2 h-2 rounded-full ${inventoryStatus === 'Complete' ? 'bg-emerald-500' : 'bg-amber-500 animate-pulse'}`}></div>
                    <span className="text-[10px] text-slate-500 font-medium">
                        {inventoryStatus === 'Complete' ? `Inv: ${inventoryCount.toLocaleString()} blocks` : `Inv: Loading (${inventoryCount.toLocaleString()}...)`}
                    </span>
                </>
            )}
        </div>
      </div>

      {/* AMENITY MAP MODAL */}
      {selectedAmenity && (
        <div className="fixed inset-0 z-[60] flex items-center justify-center p-4">
            <div className="absolute inset-0 bg-slate-900/60 backdrop-blur-sm" onClick={() => setSelectedAmenity(null)} />
            <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg relative z-10 overflow-hidden flex flex-col">
                <div className="p-4 bg-violet-900 text-white flex justify-between items-center">
                    <div>
                        <h2 className="font-bold text-lg">{selectedAmenity.name}</h2>
                        <div className="flex items-center gap-1.5 text-violet-200 text-xs mt-0.5">
                            <Navigation className="w-3 h-3" />
                            From Search Location ({searchPostal})
                        </div>
                    </div>
                    <button onClick={() => setSelectedAmenity(null)} className="text-white/70 hover:text-white">
                        <X className="w-5 h-5" />
                    </button>
                </div>
                
                {selectedAmenity.x && selectedAmenity.y ? (
                    <div className="w-full h-64 bg-slate-100 relative">
                        {/* Embedding OneMap MiniMap */}
                        <iframe 
                            src={`https://www.onemap.gov.sg/minimap/minimap.html?mapXY=${selectedAmenity.x},${selectedAmenity.y}&zoomLevel=17`} 
                            className="w-full h-full border-0"
                            title="OneMap Location"
                        />
                        <div className="absolute bottom-2 left-2 bg-white/90 text-[10px] px-2 py-1 rounded shadow text-slate-500">
                            Source: OneMap
                        </div>
                    </div>
                ) : (
                    <div className="w-full h-40 flex items-center justify-center bg-slate-50 text-slate-400 text-sm">
                        Map preview unavailable
                    </div>
                )}

                <div className="p-4 border-t border-slate-100">
                    <a 
                        href={`https://www.google.com/maps/dir/?api=1&origin=${searchPostal}&destination=${encodeURIComponent(selectedAmenity.name)}&travelmode=walking`} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="flex items-center justify-center gap-2 w-full py-3 bg-violet-600 hover:bg-violet-700 text-white font-semibold rounded-xl transition-colors"
                    >
                        <ExternalLink className="w-4 h-4" />
                        Get Directions on Google Maps
                    </a>
                </div>
            </div>
        </div>
      )}

      {/* BLOCK X-RAY MODAL */}
      {selectedBlockData && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            <div className="absolute inset-0 bg-slate-900/60 backdrop-blur-sm" onClick={() => setSelectedBlockData(null)} />
            <div className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl relative z-10 overflow-hidden flex flex-col max-h-[90vh]">
                {/* Header */}
                <div className="p-5 bg-slate-900 text-white flex justify-between items-start">
                    <div>
                        <h2 className="text-2xl font-bold">Block {selectedBlockData.block}</h2>
                        <p className="text-slate-300 text-sm">{selectedBlockData.street}</p>
                    </div>
                    <button onClick={() => setSelectedBlockData(null)} className="text-white/70 hover:text-white">
                        <X className="w-6 h-6" />
                    </button>
                </div>
                
                <div className="p-6 overflow-y-auto space-y-6">
                    
                    {/* Key Stats Row */}
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div className="p-3 bg-slate-50 rounded-xl border border-slate-100 text-center">
                            <div className="text-xs text-slate-500 uppercase font-bold mb-1">Built In</div>
                            <div className="font-bold text-lg text-slate-800">{selectedBlockData.yearCompleted || 'N/A'}</div>
                        </div>
                        <div className="p-3 bg-slate-50 rounded-xl border border-slate-100 text-center">
                            <div className="text-xs text-slate-500 uppercase font-bold mb-1">Total Units</div>
                            <div className="font-bold text-lg text-slate-800">{selectedBlockData.totalUnits || 'N/A'}</div>
                        </div>
                        <div className="p-3 bg-slate-50 rounded-xl border border-slate-100 text-center">
                            <div className="text-xs text-slate-500 uppercase font-bold mb-1">Max Floor</div>
                            <div className="font-bold text-lg text-slate-800">{selectedBlockData.maxFloor || 'N/A'}</div>
                        </div>
                        <div className="p-3 bg-blue-50 rounded-xl border border-blue-100 text-center">
                            <div className="text-xs text-blue-600 uppercase font-bold mb-1">This Unit</div>
                            <div className="font-bold text-lg text-blue-800">{selectedBlockData.storey}</div>
                        </div>
                    </div>

                    {/* Unit Mix Section */}
                    {selectedBlockData.mix && selectedBlockData.mix.length > 0 ? (
                        <div className="bg-white border border-slate-200 rounded-xl p-4">
                            <h3 className="text-sm font-bold text-slate-700 mb-4 flex items-center gap-2">
                                <Users className="w-4 h-4" /> Block Demographics (Unit Mix)
                            </h3>
                            <div className="h-48 flex items-center justify-center">
                                <ResponsiveContainer width="100%" height="100%">
                                    <PieChart>
                                        <Pie
                                            data={selectedBlockData.mix}
                                            cx="50%"
                                            cy="50%"
                                            innerRadius={40}
                                            outerRadius={60}
                                            paddingAngle={5}
                                            dataKey="value"
                                        >
                                            {selectedBlockData.mix.map((entry, index) => (
                                                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                            ))}
                                        </Pie>
                                        <RechartsTooltip />
                                        <Legend verticalAlign="middle" align="right" layout="vertical" />
                                    </PieChart>
                                </ResponsiveContainer>
                            </div>
                        </div>
                    ) : (
                        <div className="p-4 bg-slate-50 rounded-xl text-center text-sm text-slate-500 italic">
                            Detailed unit mix data not available for this specific block.
                        </div>
                    )}

                    {/* Height Analysis Context */}
                    <div className="bg-slate-50 rounded-xl p-4 border border-slate-200">
                        <h3 className="text-sm font-bold text-slate-700 mb-2 flex items-center gap-2">
                            <Eye className="w-4 h-4" /> Height Context
                        </h3>
                        {selectedBlockData.maxFloor > 0 ? (
                            <div className="text-sm text-slate-600">
                                This unit is listed as <strong>{selectedBlockData.storey}</strong>. 
                                The block is <strong>{selectedBlockData.maxFloor} storeys</strong> tall.
                                <div className="w-full bg-slate-200 h-2 rounded-full mt-2 relative">
                                    <div 
                                        className="bg-blue-500 h-2 rounded-full absolute top-0 left-0" 
                                        style={{ width: `${(parseInt(selectedBlockData.storey.split(' ')[0]) / selectedBlockData.maxFloor) * 100}%` }}
                                    ></div>
                                </div>
                                <p className="mt-2 text-xs text-slate-500">
                                    {(parseInt(selectedBlockData.storey.split(' ')[0]) / selectedBlockData.maxFloor) > 0.8 
                                        ? "🔥 This is a true Top Floor unit!" 
                                        : (parseInt(selectedBlockData.storey.split(' ')[0]) / selectedBlockData.maxFloor) > 0.5 
                                        ? "🌤️ Mid-High floor. Good balance of view and access." 
                                        : "🌳 Low floor. Good for greenery lovers or accessibility."}
                                </p>
                            </div>
                        ) : (
                            <p className="text-xs text-slate-500">Height data unavailable.</p>
                        )}
                    </div>

                    {/* Amenities Checklist */}
                    <div className="grid grid-cols-2 gap-3">
                        <div className={`p-3 rounded-lg border flex items-center gap-3 ${selectedBlockData.hasMarket ? 'bg-green-50 border-green-200 text-green-800' : 'bg-slate-50 border-slate-100 text-slate-400'}`}>
                            <Utensils className="w-5 h-5" />
                            <span className="text-sm font-medium">{selectedBlockData.hasMarket ? 'Hawker/Market Downstairs' : 'No Market in Block'}</span>
                        </div>
                        <div className={`p-3 rounded-lg border flex items-center gap-3 ${selectedBlockData.hasMultistoreyCarpark ? 'bg-blue-50 border-blue-200 text-blue-800' : 'bg-slate-50 border-slate-100 text-slate-400'}`}>
                            <Car className="w-5 h-5" />
                            <span className="text-sm font-medium">{selectedBlockData.hasMultistoreyCarpark ? 'Sheltered Carpark Connected' : 'Surface Parking Only'}</span>
                        </div>
                    </div>

                    {/* Lease Clock */}
                    {selectedBlockData.yearCompleted > 0 && (
                        <div className="border-t border-slate-100 pt-4">
                            <h3 className="text-sm font-bold text-slate-700 mb-2 flex items-center gap-2">
                                <Clock className="w-4 h-4" /> Lease Clock
                            </h3>
                            <div className="flex justify-between text-xs text-slate-500 mb-1">
                                <span>{selectedBlockData.yearCompleted}</span>
                                <span>99 Years</span>
                                <span>{selectedBlockData.yearCompleted + 99}</span>
                            </div>
                            <div className="w-full bg-slate-100 h-3 rounded-full overflow-hidden">
                                <div 
                                    className="bg-emerald-500 h-full" 
                                    style={{ width: `${((new Date().getFullYear() - selectedBlockData.yearCompleted) / 99) * 100}%` }}
                                ></div>
                            </div>
                            <p className="text-right text-xs text-emerald-600 font-bold mt-1">
                                ~{99 - (new Date().getFullYear() - selectedBlockData.yearCompleted)} years remaining
                            </p>
                        </div>
                    )}

                </div>
            </div>
        </div>
      )}

      {/* AI FLOATING ACTION BUTTON */}
      <button 
        onClick={() => { setShowAiModal(true); setAiMode('insight'); setAiResult(''); }}
        className="fixed bottom-6 right-6 bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-700 hover:to-indigo-700 text-white shadow-lg rounded-full p-4 z-50 transition-all hover:scale-105 flex items-center gap-2 font-semibold"
      >
        <Sparkles className="w-5 h-5" />
        <span className="hidden md:inline">Ask AI Consultant</span>
      </button>

      {/* AI MODAL */}
      {showAiModal && (
        <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center pointer-events-none">
          {/* Backdrop */}
          <div className="absolute inset-0 bg-slate-900/40 backdrop-blur-sm pointer-events-auto" onClick={() => setShowAiModal(false)} />
          
          {/* Modal Content */}
          <div className="bg-white w-full max-w-lg rounded-t-2xl sm:rounded-2xl shadow-2xl pointer-events-auto transform transition-all flex flex-col max-h-[90vh]">
            
            {/* Header */}
            <div className="p-5 border-b border-slate-100 flex justify-between items-center bg-gradient-to-r from-violet-50 to-indigo-50 rounded-t-2xl">
              <div className="flex items-center gap-2">
                <div className="bg-violet-600 p-1.5 rounded-lg">
                  <Sparkles className="w-4 h-4 text-white" />
                </div>
                <div>
                  <h3 className="font-bold text-slate-800">AI Property Consultant</h3>
                  <p className="text-xs text-slate-500">Powered by Gemini</p>
                </div>
              </div>
              <button onClick={() => setShowAiModal(false)} className="text-slate-400 hover:text-slate-600">
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Mode Switcher */}
            <div className="p-3 bg-slate-50 border-b border-slate-100 grid grid-cols-4 gap-2">
              <button 
                onClick={() => { setAiMode('insight'); setAiResult(''); }}
                className={`flex flex-col items-center justify-center py-2 px-1 text-[10px] font-medium rounded-lg transition-colors ${aiMode === 'insight' ? 'bg-white text-violet-700 shadow-sm border border-slate-200' : 'text-slate-500 hover:bg-slate-100'}`}
              >
                <TrendingUp className="w-4 h-4 mb-1" />
                Insight
              </button>
              <button 
                onClick={() => { setAiMode('rate'); setAiResult(''); }}
                className={`flex flex-col items-center justify-center py-2 px-1 text-[10px] font-medium rounded-lg transition-colors ${aiMode === 'rate' ? 'bg-white text-violet-700 shadow-sm border border-slate-200' : 'text-slate-500 hover:bg-slate-100'}`}
              >
                <DollarSign className="w-4 h-4 mb-1" />
                Rate
              </button>
              <button 
                onClick={() => { setAiMode('location'); setAiResult(''); }}
                className={`flex flex-col items-center justify-center py-2 px-1 text-[10px] font-medium rounded-lg transition-colors ${aiMode === 'location' ? 'bg-white text-violet-700 shadow-sm border border-slate-200' : 'text-slate-500 hover:bg-slate-100'}`}
              >
                <Map className="w-4 h-4 mb-1" />
                Town Scout
              </button>
              <button 
                onClick={() => { setAiMode('negotiate'); setAiResult(''); }}
                className={`flex flex-col items-center justify-center py-2 px-1 text-[10px] font-medium rounded-lg transition-colors ${aiMode === 'negotiate' ? 'bg-white text-violet-700 shadow-sm border border-slate-200' : 'text-slate-500 hover:bg-slate-100'}`}
              >
                <MessageSquareMore className="w-4 h-4 mb-1" />
                Negotiate
              </button>
              <button 
                onClick={() => { setAiMode('reno'); setAiResult(''); }}
                className={`flex flex-col items-center justify-center py-2 px-1 text-[10px] font-medium rounded-lg transition-colors ${aiMode === 'reno' ? 'bg-white text-violet-700 shadow-sm border border-slate-200' : 'text-slate-500 hover:bg-slate-100'}`}
              >
                <PaintBucket className="w-4 h-4 mb-1" />
                Reno Est.
              </button>
              <button 
                onClick={() => { setAiMode('vibe'); setAiResult(''); }}
                className={`flex flex-col items-center justify-center py-2 px-1 text-[10px] font-medium rounded-lg transition-colors ${aiMode === 'vibe' ? 'bg-white text-violet-700 shadow-sm border border-slate-200' : 'text-slate-500 hover:bg-slate-100'}`}
              >
                <Heart className="w-4 h-4 mb-1" />
                Vibe Check
              </button>
              <button 
                onClick={() => { setAiMode('grant'); setAiResult(''); }}
                className={`flex flex-col items-center justify-center py-2 px-1 text-[10px] font-medium rounded-lg transition-colors ${aiMode === 'grant' ? 'bg-white text-violet-700 shadow-sm border border-slate-200' : 'text-slate-500 hover:bg-slate-100'}`}
              >
                <Calculator className="w-4 h-4 mb-1" />
                Grant Wiz
              </button>
              <button 
                onClick={() => { setAiMode('fengshui'); setAiResult(''); }}
                className={`flex flex-col items-center justify-center py-2 px-1 text-[10px] font-medium rounded-lg transition-colors ${aiMode === 'fengshui' ? 'bg-white text-violet-700 shadow-sm border border-slate-200' : 'text-slate-500 hover:bg-slate-100'}`}
              >
                <Compass className="w-4 h-4 mb-1" />
                Feng Shui
              </button>
            </div>

            {/* Body */}
            <div className="p-6 overflow-y-auto">
              
              {/* --- MODE: INSIGHT --- */}
              {aiMode === 'insight' && (
                <div className="space-y-4">
                  <div className="bg-blue-50 border border-blue-100 rounded-lg p-3 text-sm text-blue-800 flex gap-2">
                    <Info className="w-4 h-4 mt-0.5 shrink-0" />
                    <p>I will analyze the currently visible data for <strong>{selectedTown} {selectedFlatType}</strong> ({stats.count} transactions).</p>
                  </div>
                  
                  {!aiResult && !aiLoading && (
                    <button 
                      onClick={handleAiAnalysis}
                      className="w-full py-3 bg-violet-600 hover:bg-violet-700 text-white font-semibold rounded-xl transition-colors flex items-center justify-center gap-2"
                    >
                      <Sparkles className="w-4 h-4" />
                      Generate Market Report
                    </button>
                  )}
                </div>
              )}

              {/* --- MODE: RATE --- */}
              {aiMode === 'rate' && (
                <div className="space-y-4">
                  <p className="text-sm text-slate-500">Found a unit on a property portal? Enter the details below and I'll compare it to the historical data.</p>
                  
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-xs font-semibold text-slate-500 uppercase mb-1">Asking Price ($)</label>
                      <input 
                        type="number" 
                        value={ratingInput.price}
                        onChange={(e) => setRatingInput({...ratingInput, price: e.target.value})}
                        placeholder="e.g. 550000"
                        className="w-full p-2.5 border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-violet-500 outline-none"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-semibold text-slate-500 uppercase mb-1">Size (sqm)</label>
                      <input 
                        type="number" 
                        value={ratingInput.size}
                        onChange={(e) => setRatingInput({...ratingInput, size: e.target.value})}
                        placeholder="e.g. 95"
                        className="w-full p-2.5 border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-violet-500 outline-none"
                      />
                    </div>
                  </div>

                  {!aiResult && !aiLoading && (
                    <button 
                      onClick={handleAiRating}
                      disabled={!ratingInput.price || !ratingInput.size}
                      className="w-full py-3 bg-violet-600 hover:bg-violet-700 disabled:bg-slate-300 disabled:text-slate-500 text-white font-semibold rounded-xl transition-colors flex items-center justify-center gap-2"
                    >
                      <Check className="w-4 h-4" />
                      Rate This Listing
                    </button>
                  )}
                </div>
              )}

              {/* --- MODE: TOWN SCOUT --- */}
              {aiMode === 'location' && (
                <div className="space-y-4">
                  <p className="text-sm text-slate-500">I can provide key insights about <strong>{selectedTown}</strong> to help you decide if it's the right place to live.</p>
                  
                  {/* Postal Code Input */}
                  <div>
                    <label className="block text-xs font-semibold text-slate-500 uppercase mb-1">Postal Code (Optional)</label>
                    <input 
                      type="text" 
                      value={postalCode}
                      onChange={(e) => setPostalCode(e.target.value)}
                      placeholder="e.g. 820123"
                      className="w-full p-2.5 border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-violet-500 outline-none"
                      maxLength={6}
                    />
                  </div>

                  {!aiResult && !aiLoading && (
                    <button 
                      onClick={handleAiLocation}
                      className="w-full py-3 bg-violet-600 hover:bg-violet-700 text-white font-semibold rounded-xl transition-colors flex items-center justify-center gap-2"
                    >
                      <Map className="w-4 h-4" />
                      Analyze Location
                    </button>
                  )}
                </div>
              )}

              {/* --- MODE: NEGOTIATE --- */}
              {aiMode === 'negotiate' && (
                <div className="space-y-4">
                  <div className="bg-blue-50 border border-blue-100 rounded-lg p-3 text-sm text-blue-800">
                    <p>I will draft a <strong>WhatsApp message</strong> for you to send to a seller's agent, using the real market average ({formatCurrency(stats.avgPrice)}) to justify your interest.</p>
                  </div>

                  {!aiResult && !aiLoading && (
                    <button 
                      onClick={handleAiNegotiate}
                      className="w-full py-3 bg-violet-600 hover:bg-violet-700 text-white font-semibold rounded-xl transition-colors flex items-center justify-center gap-2"
                    >
                      <MessageSquareMore className="w-4 h-4" />
                      Draft Message
                    </button>
                  )}
                </div>
              )}

              {/* --- MODE: RENO ESTIMATOR --- */}
              {aiMode === 'reno' && (
                <div className="space-y-4">
                   <p className="text-sm text-slate-500">Estimate renovation costs for a <strong>{selectedFlatType}</strong> (~{stats.avgSize} sqm) in {selectedTown}.</p>
                   
                   <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-xs font-semibold text-slate-500 uppercase mb-1">Current Condition</label>
                      <select 
                        value={renoInput.condition}
                        onChange={(e) => setRenoInput({...renoInput, condition: e.target.value})}
                        className="w-full p-2.5 border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-violet-500 outline-none bg-white"
                      >
                        <option value="Original/Bare">Original / Bare</option>
                        <option value="Well Maintained">Well Maintained</option>
                        <option value="Resale (Needs work)">Resale (Needs work)</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-xs font-semibold text-slate-500 uppercase mb-1">Dream Style</label>
                       <select 
                        value={renoInput.style}
                        onChange={(e) => setRenoInput({...renoInput, style: e.target.value})}
                        className="w-full p-2.5 border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-violet-500 outline-none bg-white"
                      >
                        <option value="Minimalist">Minimalist</option>
                        <option value="Scandi / Muji">Scandi / Muji</option>
                        <option value="Industrial">Industrial</option>
                        <option value="Modern Luxury">Modern Luxury</option>
                      </select>
                    </div>
                   </div>

                   {!aiResult && !aiLoading && (
                    <button 
                      onClick={handleAiRenovation}
                      className="w-full py-3 bg-violet-600 hover:bg-violet-700 text-white font-semibold rounded-xl transition-colors flex items-center justify-center gap-2"
                    >
                      <PaintBucket className="w-4 h-4" />
                      Calculate Budget
                    </button>
                  )}
                </div>
              )}

              {/* --- MODE: VIBE CHECK --- */}
              {aiMode === 'vibe' && (
                <div className="space-y-4">
                   <p className="text-sm text-slate-500">Is <strong>{selectedTown}</strong> the right fit for you? Describe your hobbies and lifestyle below.</p>
                   
                   <textarea
                      value={vibeInput}
                      onChange={(e) => setVibeInput(e.target.value)}
                      placeholder="e.g. I love nature, cycling, and late night suppers. I prefer quiet areas but need to be near a gym."
                      className="w-full p-3 border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-violet-500 outline-none h-24 resize-none"
                   />

                   {!aiResult && !aiLoading && (
                    <button 
                      onClick={handleAiVibe}
                      disabled={!vibeInput.trim()}
                      className="w-full py-3 bg-violet-600 hover:bg-violet-700 disabled:bg-slate-300 disabled:text-slate-500 text-white font-semibold rounded-xl transition-colors flex items-center justify-center gap-2"
                    >
                      <Heart className="w-4 h-4" />
                      Check Compatibility
                    </button>
                  )}
                </div>
              )}
              
              {/* --- MODE: GRANT WIZARD --- */}
              {aiMode === 'grant' && (
                <div className="space-y-4">
                  <p className="text-sm text-slate-500">Estimate your eligible CPF Housing Grants (EHG, Family Grant, PHG).</p>
                  
                  <div className="grid grid-cols-2 gap-4">
                    <div className="col-span-2">
                       <label className="block text-xs font-semibold text-slate-500 uppercase mb-1">Avg Household Income ($)</label>
                       <input 
                        type="number" 
                        value={grantInput.income}
                        onChange={(e) => setGrantInput({...grantInput, income: e.target.value})}
                        placeholder="e.g. 7000"
                        className="w-full p-2.5 border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-violet-500 outline-none"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-semibold text-slate-500 uppercase mb-1">First Timer?</label>
                      <select 
                        value={grantInput.firstTimer}
                        onChange={(e) => setGrantInput({...grantInput, firstTimer: e.target.value})}
                        className="w-full p-2.5 border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-violet-500 outline-none bg-white"
                      >
                        <option value="Yes">Yes</option>
                        <option value="No">No (Second Timer)</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-xs font-semibold text-slate-500 uppercase mb-1">Near Parents (&lt;4km)?</label>
                      <select 
                        value={grantInput.proximity}
                        onChange={(e) => setGrantInput({...grantInput, proximity: e.target.value})}
                        className="w-full p-2.5 border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-violet-500 outline-none bg-white"
                      >
                        <option value="No">No</option>
                        <option value="Yes">Yes</option>
                        <option value="Living With">Living With Parents</option>
                      </select>
                    </div>
                  </div>

                  {!aiResult && !aiLoading && (
                    <button 
                      onClick={handleAiGrant}
                      disabled={!grantInput.income}
                      className="w-full py-3 bg-violet-600 hover:bg-violet-700 disabled:bg-slate-300 disabled:text-slate-500 text-white font-semibold rounded-xl transition-colors flex items-center justify-center gap-2"
                    >
                      <Calculator className="w-4 h-4" />
                      Calculate Grants
                    </button>
                  )}
                </div>
              )}

              {/* --- MODE: FENG SHUI --- */}
              {aiMode === 'fengshui' && (
                <div className="space-y-4">
                  <p className="text-sm text-slate-500">Analyze the orientation of a unit for wind flow, sun, and energy.</p>
                  
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-xs font-semibold text-slate-500 uppercase mb-1">Main Door/Window Facing</label>
                      <select 
                        value={fengShuiInput.facing}
                        onChange={(e) => setFengShuiInput({...fengShuiInput, facing: e.target.value})}
                        className="w-full p-2.5 border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-violet-500 outline-none bg-white"
                      >
                        <option value="North">North</option>
                        <option value="South">South</option>
                        <option value="East">East</option>
                        <option value="West">West</option>
                        <option value="North-East">North-East</option>
                        <option value="North-West">North-West</option>
                        <option value="South-East">South-East</option>
                        <option value="South-West">South-West</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-xs font-semibold text-slate-500 uppercase mb-1">Floor Level</label>
                      <select 
                        value={fengShuiInput.floor}
                        onChange={(e) => setFengShuiInput({...fengShuiInput, floor: e.target.value})}
                        className="w-full p-2.5 border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-violet-500 outline-none bg-white"
                      >
                        <option value="High (above 10)">High (&gt;10)</option>
                        <option value="Mid (5-10)">Mid (5-10)</option>
                        <option value="Low (1-4)">Low (1-4)</option>
                      </select>
                    </div>
                  </div>

                  {!aiResult && !aiLoading && (
                    <button 
                      onClick={handleAiFengShui}
                      className="w-full py-3 bg-violet-600 hover:bg-violet-700 text-white font-semibold rounded-xl transition-colors flex items-center justify-center gap-2"
                    >
                      <Compass className="w-4 h-4" />
                      Read Energy
                    </button>
                  )}
                </div>
              )}

              {/* --- RESULTS SECTION --- */}
              {aiLoading && (
                <div className="py-8 text-center">
                  <RefreshCw className="w-8 h-8 text-violet-500 animate-spin mx-auto mb-3" />
                  <p className="text-sm text-slate-500 animate-pulse">Consulting AI expert...</p>
                </div>
              )}

              {aiResult && !aiLoading && (
                <div className="mt-2 animate-in fade-in slide-in-from-bottom-2 duration-500">
                  <div className="bg-slate-50 rounded-xl p-4 border border-slate-100 relative group">
                    <div className="flex items-start gap-3">
                      <div className="bg-violet-100 p-2 rounded-full shrink-0">
                         <MessageCircle className="w-4 h-4 text-violet-600" />
                      </div>
                      <div className="text-sm text-slate-700 leading-relaxed whitespace-pre-wrap">
                        {aiResult}
                      </div>
                    </div>
                    {/* Copy Button */}
                    <button 
                        onClick={() => copyToClipboard(aiResult)}
                        className="absolute top-2 right-2 p-2 bg-white rounded-lg shadow-sm border border-slate-200 text-slate-400 hover:text-violet-600 hover:border-violet-200 transition-all opacity-0 group-hover:opacity-100"
                        title="Copy to clipboard"
                    >
                        <Copy className="w-4 h-4" />
                    </button>
                  </div>
                  <button 
                    onClick={() => setAiResult('')}
                    className="mt-4 text-xs text-slate-400 hover:text-slate-600 underline w-full text-center"
                  >
                    Clear and start over
                  </button>
                </div>
              )}

            </div>
          </div>
        </div>
      )}
    </div>
  );
}