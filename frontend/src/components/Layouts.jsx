import { Outlet, useNavigate } from 'react-router-dom';

const Layout = () => {


  const isLoggedIn = () => {
    return true;
  };

  return (
  
    <div className='flex flex-col sticky'>
  {isLoggedIn() && (
    <div className='flex bg-white items-center sticky top-0 left-0 w-full p-4 z-10 shadow-md gap-2'>
      <a href='#' target='_blank' rel='noopener noreferrer'>
        {/* <img
          src=''
          alt='Logo'
          className='h-12'
        /> */}
      </a>

      <div className='flex items-center gap-2 text-center ml-auto mr-0 justify-center'>
        <span className='text-xs text-gray-800 mt-1.5'></span>
        <a href='#' target='_blank' rel='noopener noreferrer'>
          {/* <img
            src=''
            alt='Serverless Framework'
            className='h-8'
          /> */}
        </a>
      </div>
    </div>
  )}

  <div className='flex-grow sticky'>
  <Outlet />
  </div>
</div>

  );
};

export default Layout;
