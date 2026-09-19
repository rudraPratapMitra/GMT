import {useState} from "react"
function ProcessButton({data,onProcessed}){
    const[loading,setLoading]=useState(false)
    const[error,setError]=useState(null)

    const hasData=Array.isArray(data)&&data.length>0
    const handleClick=async()=>{
        setLoading(true);
        setError(null)
        try {
            await new Promise((resolve) => {
                setTimeout(()=>{
                    resolve();
                },500);
            });
        } catch (error) {
            setError(error.message)
        }finally{
            setLoading(false)
        }
    }
    return(
        <div>
            <button 
                onClick={handleClick}
                disabled={!hasData || loading}
                className="px-5 py-2.5 bg-[#0B1F3A] text-white rounded-lg disabled:opacity-60">
                    {loading?"Processing...":"Process"}
            </button> 
            {!hasData && (
        <p className="text-xs text-gray-400">Fetch data first.</p>
      )}
      {error && <p className="text-xs text-red-600">{error}</p>}
    </div>
    )
}
export default ProcessButton